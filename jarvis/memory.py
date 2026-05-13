import os
import json
import datetime
import threading
from jarvis.config import MEMORY_FILE

class MemoryStore:
    def __init__(self):
        self.facts = []
        self.lock = threading.Lock()
        self.load()

    def load(self):
        with self.lock:
            if os.path.exists(MEMORY_FILE):
                try:
                    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                        self.facts = json.load(f)
                except:
                    self.facts = []

    def save(self):
        with self.lock:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.facts, f, indent=2)

    def add(self, fact, category="other"):
        if not fact or len(fact) < 3:
            return
        fact_lower = fact.lower().strip()
        with self.lock:
            if any(f["fact"].lower() == fact_lower for f in self.facts):
                return
            self.facts.append({
                "fact": fact.strip(),
                "category": category,
                "timestamp": datetime.datetime.now().isoformat()
            })
        self.save()

    def remove(self, query):
        q = query.lower()
        with self.lock:
            before = len(self.facts)
            self.facts = [f for f in self.facts if q not in f["fact"].lower()]
            changed = len(self.facts) < before
        if changed:
            self.save()
            return True
        return False

    def clear(self):
        with self.lock:
            self.facts = []
        self.save()

    def recall_all_formatted(self):
        with self.lock:
            if not self.facts:
                return ""
            cats = {}
            for f in self.facts:
                cat = f.get("category", "other")
                cats.setdefault(cat, []).append(f["fact"])
            lines = []
            for cat in ["identity", "preference", "work", "other"]:
                if cat in cats:
                    for fact in cats[cat]:
                        lines.append(f"- [{cat}] {fact}")
            return "\n".join(lines)

    def recall(self, query=None, limit=10):
        with self.lock:
            if not self.facts:
                return ""
            if not query:
                recent = sorted(self.facts, key=lambda x: x["timestamp"], reverse=True)[:limit]
                return "\n".join(f"- {f['fact']}" for f in recent)
            query_words = set(query.lower().split())
            scored_facts = []
            for f in self.facts:
                fact_lower = f["fact"].lower()
                score = sum(1 for word in query_words if word in fact_lower)
                if score > 0:
                    scored_facts.append((score, f))
            if scored_facts:
                scored_facts.sort(key=lambda x: (x[0], x[1]["timestamp"]), reverse=True)
                results = [x[1] for x in scored_facts[:limit]]
            else:
                results = sorted(self.facts, key=lambda x: x["timestamp"], reverse=True)[:limit]
            return "\n".join(f"- {f['fact']}" for f in results)

    def recall_all(self):
        with self.lock:
            if not self.facts:
                return "I don't have any specific memories about you yet."
            total = len(self.facts)
            recent = sorted(self.facts, key=lambda x: x["timestamp"], reverse=True)
            lines = [f"  {f['fact']}" for f in recent[:5]]
            msg = "\n".join(lines)
            extra = total - 5
            if extra > 0:
                msg += f"\n  ...and {extra} more."
        return "Here is what I remember about you:\n" + msg

memory = MemoryStore()
