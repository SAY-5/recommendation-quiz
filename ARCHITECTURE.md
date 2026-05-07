# Architecture

## Data model

```
Question (id, slug, prompt, order, kind: single|multi|range)
   │ 1..N
   ▼
AnswerOption (id, question_fk, value, label, order)


Product (id, name, brand, price_cents, image_url)
   │ 1..N
   ▼
ProductAttribute (id, product_fk, key: enum, value: jsonb)
```

`ProductAttribute.value` is a JSON field so the same table can hold scalars
(`"medium"`), lists (`["fruity", "floral"]`), booleans (`true`), and numeric
ranges. The scorer dispatches on the comparison kind declared in
`apps/recommend/scoring.py` rather than on the column type.

`Recommendation` is intentionally not persisted. Scoring is deterministic
given (answers × catalog), and storing intermediate ranks would just be a
cache. The score endpoint computes on each request.

## Scoring algorithm

For every product, the score is

```
total = Σ over (question, target_value) in answers:
            Σ over rule in QUESTION_TO_ATTRIBUTES[question_slug]:
                rule.weight × match_score(rule, target_value, product[rule.attribute_key])
```

`match_score` dispatches on `rule.kind`:

| Kind | Meaning | Examples |
|---|---|---|
| `exact` | Equality | `milk_friendly: true == true` → 1.0 |
| `membership` | Set overlap | `target="fruity"` against `["fruity","floral"]` → 1.0 |
| `ordinal` | Linear fall-off on a position scale | `medium` vs `light`: distance 1 → 0.5 |
| `range` | Numeric inside an ordinal-named bucket | `caffeine="low"` (30–80mg) vs 60mg → 1.0 |

For ordinal: distance 0 → 1.0, distance 1 → 0.5, distance ≥ 2 → 0.0. Hard
incompatibility (e.g. user's brew method not in the product's compat list)
returns 0.0; the contribution drops out without docking other matches.

Each product's `reasons` is the human-readable label of its top three
contributing rules — that's what the UI shows under each card.

### Worked example

The user picks light roast, fruity, drip. The scorer evaluates two products.

```
Product A: roast=light, flavor=[fruity,floral], brew=[drip]
  roast_preference (weight=2.0, ordinal, distance=0) → 2.0 × 1.0 = 2.0
  flavor_profile  (weight=2.0, membership, fruity ∈ {fruity,floral}) → 2.0
  brew_method     (weight=3.0, membership, drip ∈ {drip}) → 3.0
  total = 7.0

Product B: roast=dark, flavor=[earthy], brew=[espresso]
  roast_preference (distance=2) → 2.0 × 0.0 = 0.0
  flavor_profile   (no overlap)  → 0.0
  brew_method      (no overlap)  → 0.0
  total = 0.0
```

Product A wins. Reasons attached: brew method (3.0), roast level (2.0),
flavor profile (2.0). On ties the lower product ID wins so results are
deterministic across pagination boundaries.

## Frontend state model

* Quiz state lives entirely in `localStorage` under
  `recommendation-quiz:answers/v1`. A schema bump goes through the version
  suffix; old entries are silently dropped on read.
* Routing: `/` lands, `/quiz/:step` is a single question per route, and
  `/results` calls `POST /api/quiz/score` with whatever the storage layer
  has. This means refresh, deep-link, and the browser back button all do
  what you'd expect.
* Each page (`LandingPage`, `QuizPage`, `ResultsPage`) is a dynamic
  `import()` so the initial route ships only what it needs.

## Performance + N+1 query analysis

The scoring service (`apps/recommend/service.py`) is structured to issue a
constant number of queries regardless of the catalog size:

1. `_load_question_slug_map(question_ids)` — one `Question.objects.filter`
   query, returning the (id, slug) tuples needed to resolve each answer to a
   scoring rule.
2. `_load_products()` — one `Product.objects.prefetch_related("attributes")`
   call. The prefetch issues one extra query for the attributes of *all*
   products in a single `IN (...)` rather than per-product.
3. `Product.objects.filter(id__in=top_ids)` — one query that fetches the
   top-N product rows for the response payload.

Total: ~3 queries per scoring call, independent of catalog or answer count.

The bench (`bench/load.py --in-process`) uses Django's
`CaptureQueriesContext` to count actual query counts per `recommend_top_n`
invocation. The 20s reference run reports ~1.8 queries per request (savings
come from a hot connection and Django's prepared-statement reuse). If the
service ever regresses to per-product attribute fetches, this number jumps
linearly with the catalog and the bench-regress gate fires.

## API error envelope

Every non-2xx response from a DRF view is wrapped by
`apps.quiz.exceptions.envelope_exception_handler`:

```json
{
  "code": "validation_error",
  "message": "answers required",
  "retryable": false,
  "request_id": "ab12cd34..."
}
```

`request_id` round-trips via the `X-Request-ID` header — clients get the same
ID back in the response, and the same ID is set by `RequestIdMiddleware` on
every successful response too. That gives you something to grep for when you
need to correlate a UI error to a server log line.

## AWS deploy-target reference

`infra/aws/` is a Terraform stub showing where each piece would land:

```
                ┌──────────────────────┐
   client ────► │  CloudFront          │
                │  - S3 origin (dist/) │
                │  - /api/* → ALB      │
                └──────┬───────────────┘
                       │
                       ▼
                ┌──────────────┐    ┌──────────────┐
                │  ALB         │───►│  ECS Fargate │ ──► RDS Postgres
                │  (api host)  │    │  (api task)  │     (private subnet)
                └──────────────┘    └──────────────┘
```

The stub provisions the VPC + RDS + ECS cluster + S3 bucket + Origin Access
Control. It deliberately stops short of a CloudFront distribution and ACM
certificate because those are the most account-specific bits (hosted zone
names, cert ARNs) and tend to drift from the canonical "what would I write?"
into "what does my account need?".

What would change for a real deployment:

1. Replace the placeholder ECR image URI in `variables.tf`.
2. Wire SSM SecureString parameters for `DJANGO_SECRET_KEY` and the RDS
   master password; reference them in the ECS task `secrets` block.
3. Add CloudFront distribution + ACM cert + Route53 alias.
4. Add CloudWatch log groups, alarms (5xx rate, ECS task failures, RDS CPU),
   and a dashboard.
5. Wire autoscaling (target tracking on ECS service CPU + ALB
   request count).
6. Promote `skip_final_snapshot = true` on RDS to `false` for prod.

None of the above requires application changes — it's all infra layer.
