# Prompt Intent Routing Design

## Goal

Make `dev-pipeline` select the smallest sufficient workflow node set from the user's prompt instead of treating every trigger as an end-to-end pipeline request.

## Design

The Skill performs routing before environment discovery. It records `target_nodes`, minimum `supporting_nodes`, explicit `excluded_nodes`, and a short reason. Explicit user instructions have priority over keyword heuristics.

Full Pipeline is selected only for explicit end-to-end intent. Review, Test, Message, Branch, and Commit can run independently. Multiple explicit actions compose their nodes without enabling unrelated phases. A completed node never falls through to the next numbered phase.

Discovery and reference loading are lazy. Review reads review references, Test reads test guidance, and Git mutation nodes resolve repository ownership. Commit Only keeps sensitive-file, repository, message, and selective-staging safeguards, but does not manufacture Review, Test, or Branch prerequisites.

## Safety boundaries

- Never inspect Git stash.
- Ask the user to select when selected changes span multiple repositories.
- Ask a clarifying question only when route ambiguity would materially change mutations.
- Actions outside the defined nodes, such as push or PR creation, require explicit user intent.

## Verification

A repository contract test asserts the router vocabulary, explicit Full Pipeline requirement, no implicit fall-through, and removal of the old always-serial rule. Existing repository routing, test reporting, CI, and packaging contracts remain green.
