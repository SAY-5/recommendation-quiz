import "@testing-library/jest-dom";
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

// Some Node + jsdom combinations leave window.localStorage as a non-functional
// object missing the Storage API methods. Install an in-memory polyfill so
// tests get deterministic web-storage semantics.
function installStoragePolyfill(): void {
  const store = new Map<string, string>();
  const polyfill: Storage = {
    get length() {
      return store.size;
    },
    clear() {
      store.clear();
    },
    getItem(key: string) {
      return store.has(key) ? (store.get(key) as string) : null;
    },
    key(index: number) {
      return Array.from(store.keys())[index] ?? null;
    },
    removeItem(key: string) {
      store.delete(key);
    },
    setItem(key: string, value: string) {
      store.set(key, String(value));
    },
  };
  Object.defineProperty(window, "localStorage", {
    configurable: true,
    value: polyfill,
  });
}

if (typeof window.localStorage?.setItem !== "function") {
  installStoragePolyfill();
}

afterEach(() => {
  cleanup();
  if (typeof window !== "undefined" && typeof window.localStorage?.clear === "function") {
    window.localStorage.clear();
  }
});
