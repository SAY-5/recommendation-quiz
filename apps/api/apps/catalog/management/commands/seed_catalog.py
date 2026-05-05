"""Seed 12 quiz questions and 30 coffee products with realistic attributes."""
from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Product, ProductAttribute
from apps.quiz.models import AnswerOption, Question, QuestionKind

QUESTIONS: list[dict[str, Any]] = [
    {
        "slug": "roast_preference",
        "prompt": "Which roast level do you usually reach for?",
        "kind": QuestionKind.SINGLE,
        "options": [
            ("light", "Light"),
            ("medium", "Medium"),
            ("dark", "Dark"),
        ],
    },
    {
        "slug": "flavor_profile",
        "prompt": "Which flavor notes appeal to you most?",
        "kind": QuestionKind.MULTI,
        "options": [
            ("fruity", "Fruity"),
            ("nutty", "Nutty"),
            ("chocolate", "Chocolate"),
            ("floral", "Floral"),
            ("earthy", "Earthy"),
        ],
    },
    {
        "slug": "brew_method",
        "prompt": "How do you brew at home?",
        "kind": QuestionKind.SINGLE,
        "options": [
            ("espresso", "Espresso machine"),
            ("drip", "Drip / pour-over"),
            ("french_press", "French press"),
            ("aeropress", "AeroPress"),
            ("coldbrew", "Cold brew"),
        ],
    },
    {
        "slug": "caffeine_sensitivity",
        "prompt": "How does caffeine treat you?",
        "kind": QuestionKind.SINGLE,
        "options": [
            ("decaf", "I prefer decaf"),
            ("low", "Sensitive — keep it light"),
            ("medium", "Standard cup is fine"),
            ("high", "Bring on the buzz"),
        ],
    },
    {
        "slug": "budget",
        "prompt": "What's your typical bag budget?",
        "kind": QuestionKind.SINGLE,
        "options": [
            ("budget", "Budget (~$10)"),
            ("mid", "Mid ($15-$25)"),
            ("premium", "Premium ($25+)"),
        ],
    },
    {
        "slug": "milk",
        "prompt": "Do you drink it with milk?",
        "kind": QuestionKind.SINGLE,
        "options": [
            (True, "Yes, usually"),
            (False, "No, black"),
        ],
    },
    {
        "slug": "acidity",
        "prompt": "How do you feel about bright, acidic coffees?",
        "kind": QuestionKind.SINGLE,
        "options": [
            ("low", "Smooth, low acidity"),
            ("medium", "Balanced"),
            ("bright", "Love a bright cup"),
        ],
    },
    {
        "slug": "drinking_time",
        "prompt": "When do you usually drink coffee?",
        "kind": QuestionKind.SINGLE,
        "options": [
            ("decaf", "Evening — keep it decaf"),
            ("low", "Afternoon — light"),
            ("medium", "Morning — standard"),
            ("high", "All day — strong"),
        ],
    },
    {
        "slug": "experience_level",
        "prompt": "How would you describe your coffee experience?",
        "kind": QuestionKind.SINGLE,
        "options": [
            ("low", "New to specialty"),
            ("medium", "Casual drinker"),
            ("bright", "Enthusiast / cupper"),
        ],
    },
    {
        "slug": "origin",
        "prompt": "Any region you gravitate toward?",
        "kind": QuestionKind.MULTI,
        "options": [
            ("fruity", "Africa (often fruity)"),
            ("chocolate", "Latin America (often chocolatey)"),
            ("earthy", "Indonesia (often earthy)"),
            ("floral", "Floral / tea-like blends"),
            ("nutty", "Nutty Brazilian-style blends"),
        ],
    },
    {
        "slug": "grind",
        "prompt": "Whole bean or pre-ground?",
        "kind": QuestionKind.SINGLE,
        "options": [
            ("espresso", "Pre-ground for espresso"),
            ("drip", "Pre-ground for drip"),
            ("french_press", "Whole bean (any brewer)"),
        ],
    },
    {
        "slug": "intensity",
        "prompt": "How bold do you want your cup?",
        "kind": QuestionKind.SINGLE,
        "options": [
            ("low", "Mellow"),
            ("medium", "Balanced"),
            ("high", "Bold and intense"),
        ],
    },
]


def _attr(p: Product, key: str, value: Any) -> None:
    ProductAttribute.objects.update_or_create(
        product=p, key=key, defaults={"value": value}
    )


PRODUCTS: list[dict[str, Any]] = [
    {
        "name": "Yirgacheffe Single Origin",
        "brand": "Highland Roasters",
        "price_cents": 2400,
        "attrs": {
            "roast_level": "light",
            "flavor_profile": ["floral", "fruity"],
            "caffeine_mg": 95,
            "brew_method_compatibility": ["drip", "aeropress", "coldbrew"],
            "price_tier": "mid",
            "milk_friendly": False,
            "acidity": "bright",
        },
    },
    {
        "name": "Sumatra Mandheling",
        "brand": "Volcanic Bean Co.",
        "price_cents": 1800,
        "attrs": {
            "roast_level": "dark",
            "flavor_profile": ["earthy", "chocolate"],
            "caffeine_mg": 130,
            "brew_method_compatibility": ["french_press", "drip", "espresso"],
            "price_tier": "mid",
            "milk_friendly": True,
            "acidity": "low",
        },
    },
    {
        "name": "Colombia Supremo",
        "brand": "Andes Trade",
        "price_cents": 1500,
        "attrs": {
            "roast_level": "medium",
            "flavor_profile": ["nutty", "chocolate"],
            "caffeine_mg": 110,
            "brew_method_compatibility": ["drip", "espresso", "french_press", "aeropress"],
            "price_tier": "budget",
            "milk_friendly": True,
            "acidity": "medium",
        },
    },
    {
        "name": "Ethiopia Sidamo",
        "brand": "Rift Valley Coffee",
        "price_cents": 2200,
        "attrs": {
            "roast_level": "light",
            "flavor_profile": ["fruity", "floral"],
            "caffeine_mg": 100,
            "brew_method_compatibility": ["drip", "aeropress"],
            "price_tier": "mid",
            "milk_friendly": False,
            "acidity": "bright",
        },
    },
    {
        "name": "Brazil Cerrado",
        "brand": "Cerrado Direct",
        "price_cents": 1300,
        "attrs": {
            "roast_level": "medium",
            "flavor_profile": ["nutty", "chocolate"],
            "caffeine_mg": 120,
            "brew_method_compatibility": ["espresso", "drip", "french_press"],
            "price_tier": "budget",
            "milk_friendly": True,
            "acidity": "low",
        },
    },
    {
        "name": "Italian Espresso Blend",
        "brand": "Caffe Roma",
        "price_cents": 1700,
        "attrs": {
            "roast_level": "dark",
            "flavor_profile": ["chocolate", "nutty"],
            "caffeine_mg": 140,
            "brew_method_compatibility": ["espresso"],
            "price_tier": "mid",
            "milk_friendly": True,
            "acidity": "low",
        },
    },
    {
        "name": "Kenya AA Peaberry",
        "brand": "Highland Roasters",
        "price_cents": 2800,
        "attrs": {
            "roast_level": "light",
            "flavor_profile": ["fruity"],
            "caffeine_mg": 105,
            "brew_method_compatibility": ["drip", "aeropress", "coldbrew"],
            "price_tier": "premium",
            "milk_friendly": False,
            "acidity": "bright",
        },
    },
    {
        "name": "Guatemala Antigua",
        "brand": "Volcanic Bean Co.",
        "price_cents": 1900,
        "attrs": {
            "roast_level": "medium",
            "flavor_profile": ["chocolate", "nutty"],
            "caffeine_mg": 115,
            "brew_method_compatibility": ["drip", "espresso", "french_press"],
            "price_tier": "mid",
            "milk_friendly": True,
            "acidity": "medium",
        },
    },
    {
        "name": "Costa Rica Tarrazu",
        "brand": "Andes Trade",
        "price_cents": 2100,
        "attrs": {
            "roast_level": "medium",
            "flavor_profile": ["chocolate", "fruity"],
            "caffeine_mg": 110,
            "brew_method_compatibility": ["drip", "espresso", "aeropress"],
            "price_tier": "mid",
            "milk_friendly": True,
            "acidity": "medium",
        },
    },
    {
        "name": "Mexico Chiapas Decaf",
        "brand": "Decaf Lab",
        "price_cents": 1600,
        "attrs": {
            "roast_level": "medium",
            "flavor_profile": ["chocolate", "nutty"],
            "caffeine_mg": 5,
            "brew_method_compatibility": ["drip", "espresso", "french_press"],
            "price_tier": "mid",
            "milk_friendly": True,
            "acidity": "low",
        },
    },
    {
        "name": "Swiss Water Decaf",
        "brand": "Decaf Lab",
        "price_cents": 1800,
        "attrs": {
            "roast_level": "medium",
            "flavor_profile": ["chocolate"],
            "caffeine_mg": 5,
            "brew_method_compatibility": ["drip", "aeropress"],
            "price_tier": "mid",
            "milk_friendly": True,
            "acidity": "medium",
        },
    },
    {
        "name": "French Roast Bold",
        "brand": "Caffe Roma",
        "price_cents": 1400,
        "attrs": {
            "roast_level": "dark",
            "flavor_profile": ["earthy", "chocolate"],
            "caffeine_mg": 145,
            "brew_method_compatibility": ["drip", "french_press", "espresso"],
            "price_tier": "budget",
            "milk_friendly": True,
            "acidity": "low",
        },
    },
    {
        "name": "Honduras Marcala",
        "brand": "Andes Trade",
        "price_cents": 1700,
        "attrs": {
            "roast_level": "medium",
            "flavor_profile": ["chocolate", "nutty"],
            "caffeine_mg": 105,
            "brew_method_compatibility": ["drip", "espresso", "aeropress"],
            "price_tier": "mid",
            "milk_friendly": True,
            "acidity": "medium",
        },
    },
    {
        "name": "Panama Geisha",
        "brand": "Highland Roasters",
        "price_cents": 4500,
        "attrs": {
            "roast_level": "light",
            "flavor_profile": ["floral", "fruity"],
            "caffeine_mg": 90,
            "brew_method_compatibility": ["drip", "aeropress"],
            "price_tier": "premium",
            "milk_friendly": False,
            "acidity": "bright",
        },
    },
    {
        "name": "Burundi Kayanza",
        "brand": "Rift Valley Coffee",
        "price_cents": 2300,
        "attrs": {
            "roast_level": "light",
            "flavor_profile": ["fruity", "floral"],
            "caffeine_mg": 95,
            "brew_method_compatibility": ["drip", "aeropress", "coldbrew"],
            "price_tier": "mid",
            "milk_friendly": False,
            "acidity": "bright",
        },
    },
    {
        "name": "Vietnam Robusta",
        "brand": "Mekong Coffee",
        "price_cents": 1100,
        "attrs": {
            "roast_level": "dark",
            "flavor_profile": ["earthy", "chocolate"],
            "caffeine_mg": 200,
            "brew_method_compatibility": ["espresso", "french_press"],
            "price_tier": "budget",
            "milk_friendly": True,
            "acidity": "low",
        },
    },
    {
        "name": "Cold Brew Blend",
        "brand": "Iceberg Roasters",
        "price_cents": 1900,
        "attrs": {
            "roast_level": "medium",
            "flavor_profile": ["chocolate", "nutty"],
            "caffeine_mg": 125,
            "brew_method_compatibility": ["coldbrew", "drip"],
            "price_tier": "mid",
            "milk_friendly": True,
            "acidity": "low",
        },
    },
    {
        "name": "Single Origin Espresso",
        "brand": "Caffe Roma",
        "price_cents": 2200,
        "attrs": {
            "roast_level": "medium",
            "flavor_profile": ["chocolate", "fruity"],
            "caffeine_mg": 130,
            "brew_method_compatibility": ["espresso"],
            "price_tier": "mid",
            "milk_friendly": True,
            "acidity": "medium",
        },
    },
    {
        "name": "House Drip Blend",
        "brand": "Common Grounds",
        "price_cents": 1200,
        "attrs": {
            "roast_level": "medium",
            "flavor_profile": ["nutty", "chocolate"],
            "caffeine_mg": 110,
            "brew_method_compatibility": ["drip", "french_press"],
            "price_tier": "budget",
            "milk_friendly": True,
            "acidity": "medium",
        },
    },
    {
        "name": "Rwanda Nyamasheke",
        "brand": "Rift Valley Coffee",
        "price_cents": 2400,
        "attrs": {
            "roast_level": "light",
            "flavor_profile": ["fruity", "floral"],
            "caffeine_mg": 100,
            "brew_method_compatibility": ["drip", "aeropress"],
            "price_tier": "mid",
            "milk_friendly": False,
            "acidity": "bright",
        },
    },
    {
        "name": "Peru Cajamarca Organic",
        "brand": "Andes Trade",
        "price_cents": 1800,
        "attrs": {
            "roast_level": "medium",
            "flavor_profile": ["chocolate", "nutty"],
            "caffeine_mg": 105,
            "brew_method_compatibility": ["drip", "french_press", "aeropress"],
            "price_tier": "mid",
            "milk_friendly": True,
            "acidity": "medium",
        },
    },
    {
        "name": "Java Estate",
        "brand": "Mekong Coffee",
        "price_cents": 1700,
        "attrs": {
            "roast_level": "dark",
            "flavor_profile": ["earthy", "chocolate"],
            "caffeine_mg": 135,
            "brew_method_compatibility": ["french_press", "drip", "espresso"],
            "price_tier": "mid",
            "milk_friendly": True,
            "acidity": "low",
        },
    },
    {
        "name": "Ristretto Dark",
        "brand": "Caffe Roma",
        "price_cents": 1500,
        "attrs": {
            "roast_level": "dark",
            "flavor_profile": ["chocolate", "earthy"],
            "caffeine_mg": 150,
            "brew_method_compatibility": ["espresso"],
            "price_tier": "budget",
            "milk_friendly": True,
            "acidity": "low",
        },
    },
    {
        "name": "Tanzania Peaberry",
        "brand": "Rift Valley Coffee",
        "price_cents": 2200,
        "attrs": {
            "roast_level": "light",
            "flavor_profile": ["fruity"],
            "caffeine_mg": 100,
            "brew_method_compatibility": ["drip", "aeropress", "coldbrew"],
            "price_tier": "mid",
            "milk_friendly": False,
            "acidity": "bright",
        },
    },
    {
        "name": "Decaf Espresso Blend",
        "brand": "Decaf Lab",
        "price_cents": 1900,
        "attrs": {
            "roast_level": "dark",
            "flavor_profile": ["chocolate", "nutty"],
            "caffeine_mg": 5,
            "brew_method_compatibility": ["espresso"],
            "price_tier": "mid",
            "milk_friendly": True,
            "acidity": "low",
        },
    },
    {
        "name": "Nicaragua Jinotega",
        "brand": "Andes Trade",
        "price_cents": 1600,
        "attrs": {
            "roast_level": "medium",
            "flavor_profile": ["chocolate", "nutty"],
            "caffeine_mg": 110,
            "brew_method_compatibility": ["drip", "espresso", "french_press"],
            "price_tier": "budget",
            "milk_friendly": True,
            "acidity": "medium",
        },
    },
    {
        "name": "Bali Kintamani",
        "brand": "Mekong Coffee",
        "price_cents": 2000,
        "attrs": {
            "roast_level": "medium",
            "flavor_profile": ["earthy", "fruity"],
            "caffeine_mg": 115,
            "brew_method_compatibility": ["drip", "french_press", "aeropress"],
            "price_tier": "mid",
            "milk_friendly": True,
            "acidity": "medium",
        },
    },
    {
        "name": "Premium Geisha Reserve",
        "brand": "Highland Roasters",
        "price_cents": 5500,
        "attrs": {
            "roast_level": "light",
            "flavor_profile": ["floral", "fruity"],
            "caffeine_mg": 85,
            "brew_method_compatibility": ["drip", "aeropress"],
            "price_tier": "premium",
            "milk_friendly": False,
            "acidity": "bright",
        },
    },
    {
        "name": "Morning Drip Roast",
        "brand": "Common Grounds",
        "price_cents": 1100,
        "attrs": {
            "roast_level": "medium",
            "flavor_profile": ["nutty", "chocolate"],
            "caffeine_mg": 105,
            "brew_method_compatibility": ["drip"],
            "price_tier": "budget",
            "milk_friendly": True,
            "acidity": "medium",
        },
    },
    {
        "name": "Espresso Forte",
        "brand": "Caffe Roma",
        "price_cents": 1900,
        "attrs": {
            "roast_level": "dark",
            "flavor_profile": ["chocolate"],
            "caffeine_mg": 155,
            "brew_method_compatibility": ["espresso"],
            "price_tier": "mid",
            "milk_friendly": True,
            "acidity": "low",
        },
    },
]


class Command(BaseCommand):
    help = "Load 12 quiz questions and 30 coffee products into the database."

    def handle(self, *args: Any, **options: Any) -> None:
        with transaction.atomic():
            self._seed_questions()
            self._seed_products()
        self.stdout.write(self.style.SUCCESS("Seed complete."))

    def _seed_questions(self) -> None:
        for order, q in enumerate(QUESTIONS, start=1):
            question, _ = Question.objects.update_or_create(
                slug=q["slug"],
                defaults={
                    "prompt": q["prompt"],
                    "kind": q["kind"],
                    "order": order,
                },
            )
            for opt_order, (value, label) in enumerate(q["options"], start=1):
                AnswerOption.objects.update_or_create(
                    question=question,
                    value=str(value),
                    defaults={"label": label, "order": opt_order},
                )
        self.stdout.write(f"Seeded {len(QUESTIONS)} questions.")

    def _seed_products(self) -> None:
        for spec in PRODUCTS:
            product, _ = Product.objects.update_or_create(
                brand=spec["brand"],
                name=spec["name"],
                defaults={
                    "price_cents": spec["price_cents"],
                    "image_url": spec.get("image_url", ""),
                },
            )
            for key, value in spec["attrs"].items():
                _attr(product, key, value)
        self.stdout.write(f"Seeded {len(PRODUCTS)} products.")
