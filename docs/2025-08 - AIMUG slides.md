# SETUP

* Create branch: add-tags
* Run dev server and click through to make sure it works
* Open up https://gamma.app/docs/My-Claude-Code-Workflow-8r9232jftsrw410 and make sure it's up to date




---


# Introduction

I'm going to be sharing some of the best practices I've found with `claude code` as my coding agent.

I am constantly evolving this, so this is just a snapshot in time.

I'll be using a demo app of a `PromptManager` and a very simple feature so that we can get through this.

---


# Context is Everything

You agent is only as good as the context you give it.

Garbage in, garbage out.

But what isn't obvious is you have 2 contexts to sync:

1. Claude <-> My Brain (so it knows what I want to change)
2. Claude <-> Codebase (so it knows how to change it)

---


# Claude <-> My Brain Synchronization: Part 1

The goal is to get everything in my brain into a document that claude can use so that it builds the right thing.

Even for something as simple as "provide the ability to delete posts" there are a lot of decisions to make

**Provide a visual of a lot of different paths you can go down in a decision tree**

Getting the details right on the front end eliminates a lot of the bad paths

It's WAAAAAY less expensive to get the details right on the front end than it is to fix it later.

---


# Claude <-> My Brain Synchronization: Part 2

Keep changes small, iterate and review each step of the way

That way if a mistake is made early on, you can course correct so that mistakes don't compound

**Show visual of course correction down decision tree**

---

# My Issue Tracking Stack

I use Linear for roadmap management (planning)

I use Taskmaster for breaking down a feature into smaller tasks (execution)

(this is just my setup, there are many good options out there)

---


# Secret Weapons: Custom commands and subagents

https://x.com/buildkata/status/1949884380890972495

commands follow instructions really well

subagents can do specialized tasks really well and not pollute your context


My go-to pattern for workflows in claude code is now:

custom commands == coordinators
subagents == technical specialists


---



# My Workflow: Phase 1 (build up requirements)


I PICK AND CHOOSE which steps to take given feature complexity, uncertainty, etc:

1. /pm/linear-refine <linear ticket number> - Flesh out the requiremetns for a given linear ticket (use cases & functional requirements)
2. /dev/architecture-recommendation <linear ticket number> - Evaluate different architectures / solutions
3. /dev/prd-generation <linear ticket number> - Generate a PRD
4. create a branch & create tasks:
   - `tm parse-prd ...`
   - `tm expand --all`

---

# Claude <-> Codebase Synchronization


I build up context with /build-context



---


# My Workflow: Phase 2 (build the feature)


Then, I iterate for each task:

1. Claude code build features until linting & tests pass
2. /regression-test/test-recent-changes - Run regression tests
3. I review the code
4. Stage or commit changes (to create clean slate for next iteration)

---


# Other Context Management Pro Tips

These are "on demand" tools that you can use to avoid compaction (or handle it well if you have to)

* Use Double-ESC to go back to a previous clean state with good context
* Set up a good context and use /resume or --resume to clone it
* Use /save-context and /restore-context to get around compaction (fallback; not my preferred approach)

Bonus: Use --continue to preserve state between restarts

---

