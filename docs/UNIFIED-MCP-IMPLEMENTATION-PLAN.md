# Unified MCP Implementation Plan

## Purpose

The KG repository family currently implements Model Context Protocol servers
independently. PyCodeKG, TypeScriptKG, DocKG, DiaryKG, MemoryKG, GutenbergKG,
AgentKG, MetaboKG, and KGRAG each own some combination of:

- MCP server construction and transport startup
- runtime initialization and resource ownership
- command-line parsing and path resolution
- tool registration and schema generation
- result serialization and error handling
- startup diagnostics
- compatibility tests

The repeated implementations have drifted into several MCP API families and
dependency ranges. Closely related packages now solve the same lifecycle problem
in different ways, while PyCodeKG and TypeScriptKG duplicate nearly identical
large tool surfaces.

This plan defines a unified implementation in `kgmodule-utils`. Domain behavior
will remain in its owning package. Existing package commands and public tool
names will remain compatible. KGRAG will become the optional single MCP gateway
for users who want one endpoint across multiple registered knowledge graphs.

This document is a companion to
[`MCP-CONSOLIDATION-PLAN.md`](MCP-CONSOLIDATION-PLAN.md). That document records
the immediate dependency-bounding work and its narrower bootstrap proposal.
This document describes the target architecture and cross-repository migration.

## Status

**Planning only. No implementation has started under this plan.**

## Goals

1. Maintain one implementation of MCP lifecycle, registration, serialization,
   transport, and compatibility behavior.
2. Keep KG-specific query, analysis, registry, memory, and media behavior in the
   package that owns it.
3. Preserve existing console commands, tool names, signatures, defaults, and
   result formats during migration.
4. Eliminate handwritten MCP schemas and dispatch tables.
5. Support text, JSON, Markdown, structured, asynchronous, and image results.
6. Allow packages to run as independent MCP servers.
7. Allow KGRAG to expose a single, namespaced gateway across registered KGs.
8. Preserve dependency isolation where KG packages cannot safely share one
   Python environment.
9. Make MCP version changes and conformance decisions once in `kgmodule-utils`.

## Non-goals

- Moving domain algorithms into `kgmodule-utils`
- Replacing KGRAG's federation and registry abstractions
- Renaming public tools as part of the initial migration
- Requiring every KG package in one Python environment
- Removing standalone per-package MCP commands
- Adding speculative MCP features unrelated to existing servers

## Current-state findings

### Server families

The repositories currently use three distinct implementation patterns:

| Pattern | Repositories | Characteristics |
|---|---|---|
| Large decorator-based servers | PyCodeKG, TypeScriptKG | Nineteen nearly identical tools; module globals; server, domain adapters, analysis, snapshots, and CLI startup combined in large modules |
| Small decorator-based servers | DocKG, DiaryKG, MemoryKG | Repeated initialization, path handling, query/pack/stats adapters, diagnostics, and transport startup |
| Low-level manual MCP servers | KGRAG, AgentKG | Handwritten JSON schemas, explicit tool lists, and large name-based dispatch functions |
| Async media server | GutenbergKG | Standalone FastMCP, asynchronous image tools, worker-thread execution, and image result handling |

MetaboKG should be included in the migration inventory because it also exposes
MCP tools, although its server is constructed through a factory rather than at
module import.

### Duplication boundary

The duplication is not limited to server startup. It occurs at several levels:

- transport and server construction
- runtime state and lazy initialization
- common KG capabilities such as query, pack, stats, and node lookup
- code-KG capabilities such as callers, centrality, analysis, CodeRank, and
  snapshots
- schema generation and documentation synchronization
- JSON and Markdown output formatting
- error translation and startup warnings
- import-level compatibility tests

The correct shared boundary is therefore broader than an import shim, but
narrower than a universal KG server class.

### Existing foundation

`kgmodule-utils` is already the shared dependency for the KG family and owns
common KG types, stores, semantic infrastructure, snapshots, and pipeline
contracts. It is the natural home for the MCP implementation.

Its core installation is intentionally dependency-free. MCP support must
therefore be delivered through an optional extra and isolated subpackage.

KGRAG already provides the cross-KG registry and adapter boundary. It should
remain responsible for federation and become the optional unified gateway rather
than moving registry behavior into `kgmodule-utils`.

## Target architecture

```text
MCP client
   |
   +-- standalone mode ------------------------------+
   |                                                |
   |     pycodekg-mcp / dockg-mcp / ...             |
   |          |                                     |
   |          v                                     |
   |     package provider + tool profiles           |
   |          |                                     |
   +----------+-------------------------------------+
              |
              v
       kg_utils.mcp runtime
       - server lifecycle
       - tool registration
       - schema generation
       - transports
       - serialization
       - error mapping
       - conformance

MCP client
   |
   +-- gateway mode --> KGRAG MCP gateway
                          |
                          +-- registry/corpus/person tools
                          +-- namespaced domain tools
                          +-- isolated KG workers where required
```

Each domain package will contain only:

- a provider that constructs and closes its runtime resources
- its server metadata and default configuration
- its selected shared tool profiles
- domain-specific tool callbacks
- compatibility aliases for existing public tool names
- a thin CLI entry point

## Shared package design

Add `kg_utils.mcp` behind a new `mcp` optional dependency extra.

### Server specification

`ServerSpec` describes the public server:

- server name and version
- instructions
- enabled transports
- selected tool profiles
- public aliases
- optional namespace

The registered tool manifest should be generated from this specification and the
actual registered callables. Server instructions must not maintain a second,
manually synchronized list of signatures.

### Runtime configuration

`RuntimeConfig` contains shared operational configuration:

- repository or corpus root
- graph database
- vector backend paths
- model
- transport
- registry path when applicable
- domain-specific options in an explicit extension mapping

Shared path helpers will resolve relative paths against the configured root.
They will not assume that all domains use the same directory names or vector
backend.

### Provider protocol

A small provider protocol will own domain resources:

- `validate()` checks required artifacts without loading the full KG.
- `open()` constructs or returns the lazily initialized runtime.
- `close()` deterministically releases stores, models, registries, and temporary
  resources.
- `capabilities()` declares supported tool profiles.

Providers replace module-level `_kg` and `_snapshot_mgr` globals. Tests can
inject fake providers without importing models or opening production databases.

### MCP runtime

`MCPRuntime` will:

- construct the supported FastMCP server
- register shared and domain-specific tools
- own provider initialization and shutdown
- map exceptions to consistent MCP errors
- serialize supported result types
- emit diagnostics to stderr
- start the selected transport

The runtime must support synchronous and asynchronous handlers. It must not force
all results into text because GutenbergKG returns images and future tools may use
structured content.

### Tool registration

Prefer composable registration functions over a universal server superclass.
Each profile registers a coherent capability set against explicit callbacks.

Proposed profiles:

| Profile | Capabilities |
|---|---|
| `core` | query, pack, stats, node lookup |
| `code_navigation` | callers, list/find node, definition lookup, explain |
| `structural_analysis` | centrality, bridge centrality, framework nodes, full analysis |
| `coderank` | global ranking, ranked query, rank explanation |
| `snapshots` | snapshot list, show, and diff |
| `registry` | KG list, information, availability, and registry stats |
| `corpora` | corpus CRUD, scoped query, and scoped pack |
| `persons` | person-corpus CRUD, metadata, query, and pack |
| `memory` | ingest, assemble, prune, topics, tasks, and profile |
| `media` | image generation and corpus-grounded image generation |

Profiles define internal capability names. Packages control their public names.
For example, `query_codebase`, `query_docs`, and `query_diary` may all use the
same registration machinery without becoming one public tool name.

### Serialization and errors

The shared layer will support:

- JSON from mappings and data models
- Markdown and plain text
- native structured MCP content
- FastMCP image results
- lists of supported content blocks

Errors will distinguish:

- invalid arguments
- unavailable optional capability
- missing or stale KG artifacts
- unknown registry entries
- domain execution failures
- internal server failures

Server implementations must not silently turn every exception into a successful
text result. Mutating tools require particularly clear failure semantics.

## Public compatibility policy

The first migration is compatibility-preserving.

- Console scripts remain available.
- Tool names remain unchanged.
- Parameters, types, defaults, and required/optional status remain unchanged.
- Output formats remain unchanged unless an existing behavior is demonstrably
  invalid.
- Existing client configuration remains valid.
- New canonical names may be added as aliases, but old names are not removed.

Before migrating a server, capture its public tool manifest as a golden fixture:

- tool name
- description
- input schema
- output content type
- mutation/read-only classification

Any intentional change requires an explicit package-level API decision and
release note.

## Implementation phases

### Phase 1: Contract and inventory

1. Inventory every MCP server in the KG repository family.
2. Record tool manifests, transports, dependency versions, initialization
   behavior, result types, and resource lifecycles.
3. Compare PyCodeKG and TypeScriptKG signatures and outputs tool by tool.
4. Classify shared capabilities and domain-only tools.
5. Decide the supported FastMCP distribution and major version using clean
   environment tests against the actual package artifacts.
6. Write the provider, runtime, profile, serialization, and error contracts.

**Exit criteria**

- Every server and public tool is represented in the inventory.
- Intentional and accidental cross-repository differences are identified.
- The shared contract supports text, async, image, mutation, and federation use
  cases without repository-specific imports.

### Phase 2: Build `kg_utils.mcp`

1. Add the optional `mcp` dependency extra.
2. Implement server specification and runtime configuration.
3. Implement provider lifecycle management.
4. Implement runtime construction, registration, shutdown, and transports.
5. Implement serializers and error mapping.
6. Implement the `core` profile.
7. Add manifest generation and conformance-test helpers.
8. Document how a domain package defines a provider and registers custom tools.

**Exit criteria**

- `kgmodule-utils` remains importable without MCP dependencies.
- A synthetic KG can expose core tools through stdio in a test.
- Runtime initialization and shutdown are deterministic.
- Registered schemas are derived from typed callables.

### Phase 3: DocKG reference migration

Migrate DocKG first because it is the smallest representative query/pack server.

1. Implement a DocKG provider.
2. Register the core profile with existing public aliases.
3. Replace repeated path and startup plumbing with the shared runtime.
4. Preserve `dockg-mcp` and all current tools.
5. Run manifest comparison and protocol-level smoke tests.
6. Refine the shared API before migrating another repository.

**Exit criteria**

- No public DocKG MCP API drift.
- The DocKG server contains domain configuration and callbacks, not generic
  lifecycle plumbing.
- The shared API remains small and comprehensible after a real migration.

### Phase 4: Code-KG consolidation

Migrate PyCodeKG and TypeScriptKG as one coordinated design effort.

1. Resolve their manifest differences explicitly.
2. Implement code navigation, structural analysis, CodeRank, and snapshot
   profiles.
3. Define the code-KG callback protocol required by those profiles.
4. Implement providers in both repositories.
5. Replace duplicated tool bodies with profile registration.
6. Preserve each server's instructions and domain identity.
7. Ensure runtime tools, module documentation, and MCP instructions remain
   synchronized automatically.

**Exit criteria**

- Shared capabilities have one implementation.
- Both packages pass the same conformance suite.
- Package-specific behavior is expressed through callbacks or configuration,
  not conditionals in `kg_utils`.
- Existing PyCodeKG and TypeScriptKG clients require no configuration changes.

### Phase 5: Small KG migrations

Migrate DiaryKG and MemoryKG using the validated core profile.

1. Add providers.
2. Preserve current query, pack, node, and stats names.
3. Register aliases where public naming differs.
4. Remove duplicated startup and lifecycle code.

Evaluate MetaboKG in this phase. Use shared structural profiles only where its
semantics genuinely match; otherwise keep its domain tools custom while sharing
the runtime.

**Exit criteria**

- All small KG servers use the shared lifecycle.
- Domain-specific relation sets and formatting remain package-owned.

### Phase 6: KGRAG and AgentKG migration

Convert the low-level manual servers to typed registration.

For KGRAG:

1. Keep registry, corpus, person, and federation logic in KGRAG.
2. Implement registry, corpora, and persons profiles using KGRAG callbacks.
3. Replace handwritten schemas and the large name-based dispatcher.
4. Preserve every `kgrag_*` tool name and behavior.

For AgentKG:

1. Implement an AgentKG provider with explicit repo, person, and session scope.
2. Register the memory profile.
3. Replace per-branch open/close repetition with provider-managed contexts.
4. Preserve all existing defaults and public names.

**Exit criteria**

- Neither repository manually maintains JSON schemas.
- Unknown tools and execution errors use shared error semantics.
- Mutating tools have explicit annotations and tests.

### Phase 7: GutenbergKG migration

Use GutenbergKG to validate the non-text and asynchronous extension points.

1. Register its tools through the media profile.
2. Preserve async handlers and worker-thread execution.
3. Preserve native image results.
4. Keep image generation, prompt rewriting, compression, and size policy in
   GutenbergKG.
5. Define ownership and cleanup of temporary image artifacts.

**Exit criteria**

- Generated images remain valid MCP image results.
- The shared runtime does not impose text-only serialization.
- Blocking inference does not block the MCP event loop.

### Phase 8: KGRAG unified gateway

Add an optional gateway mode after standalone migrations are stable.

Two modes will remain available:

- `federated`: KGRAG registry, corpus, person, query, and pack tools only.
- `gateway`: federated tools plus selected domain tools.

Gateway tools must be namespaced to avoid collisions:

```text
code.query_codebase
docs.pack_docs
memory.ingest
gutenberg.generate_image
```

The gateway must support two execution strategies:

- in-process registration when dependency sets are compatible
- isolated worker processes when a registered KG uses a different environment
  or expensive runtime

The registry should determine package location, environment, capabilities, and
availability. Gateway startup must not eagerly load every registered model or
database.

**Exit criteria**

- A client may configure only KGRAG and access selected federated and deep-domain
  tools.
- One unavailable KG does not prevent gateway startup.
- Tool namespace collisions are impossible.
- Standalone package servers continue to work.

### Phase 9: Ecosystem cleanup

1. Remove obsolete compatibility implementations after every consumer has
   migrated.
2. Align dependency ranges across repositories.
3. Update MCP documentation and client configuration examples.
4. Add release notes and migration notes per package.
5. Decide whether canonical cross-domain aliases should become recommended,
   without removing existing names.

## Testing strategy

### Shared tests in `kgmodule-utils`

- server construction for every supported transport
- provider lazy initialization and one-time reuse
- deterministic shutdown after success and failure
- schema generation from sync and async callables
- JSON, Markdown, structured, and image serialization
- exception-to-MCP error mapping
- manifest generation
- missing optional dependency behavior
- stderr-only diagnostics for stdio servers

### Per-repository conformance tests

- expected server imports successfully
- console entry point resolves
- golden tool manifest matches
- public defaults and schemas remain stable
- representative tool call reaches the domain callback
- missing database/index behavior is actionable
- resources close after tool execution and shutdown
- instructions describe the registered runtime surface

### Gateway tests

- namespace generation and collision rejection
- selective capability exposure
- lazy worker startup
- isolated-environment execution
- partial availability
- concurrent calls to different KGs
- worker failure and restart behavior
- mutation-tool routing

### Release verification

For each migrated repository:

1. Build and install its wheel in a clean environment.
2. Run the MCP conformance suite.
3. Start the console command over stdio.
4. List tools through an MCP client.
5. Invoke at least one representative tool.
6. Compare the resulting manifest with the pre-migration fixture.

## Rollout order

The dependency order is:

1. `kgmodule-utils` shared implementation
2. DocKG reference migration
3. PyCodeKG and TypeScriptKG
4. DiaryKG, MemoryKG, and MetaboKG
5. KGRAG and AgentKG
6. GutenbergKG
7. KGRAG gateway mode
8. Compatibility cleanup

Each repository remains independently releasable. A migration does not depend on
all later repositories moving in the same release.

## Risks and mitigations

### Shared-package blast radius

A defective `kg_utils.mcp` release could affect several servers.

Mitigations:

- optional MCP extra
- strict semantic-version floor in migrated packages
- shared conformance suite plus package-specific golden manifests
- reference migration before broad adoption
- no auto-upgrade across unverified major versions

### Over-generalization

A universal abstraction could accumulate repository-specific switches.

Mitigations:

- small provider protocol
- composable profiles
- explicit callbacks
- custom tools remain package-owned
- no domain-package imports from `kg_utils`

### Public API drift

Decorator migration can change schemas even when Python behavior appears equal.

Mitigations:

- capture manifests before migration
- compare names, descriptions, schemas, defaults, and result types
- preserve aliases
- require explicit review for intentional changes

### Dependency conflicts

Some KG packages have incompatible or expensive dependency sets.

Mitigations:

- standalone servers remain supported
- gateway supports isolated workers
- capability discovery does not require importing the domain package
- model and database initialization remain lazy

### Resource lifetime errors

Long-running gateways increase the consequences of leaked stores, models, and
temporary files.

Mitigations:

- provider-owned lifecycle
- context-managed resources
- shutdown tests
- explicit temporary-artifact ownership
- worker isolation for unstable or heavyweight runtimes

## Decisions required before implementation

1. Select the supported FastMCP distribution and major version after testing the
   actual clean-install candidates.
2. Decide whether MCP remains an optional extra or becomes a core dependency in
   packages that publish unconditional MCP console scripts.
3. Approve the provider and tool-profile contracts.
4. Approve namespace syntax for KGRAG gateway tools.
5. Decide whether isolated workers use the existing KGRAG worker mechanism or a
   new shared worker protocol.
6. Define the deprecation policy for any future canonical tool aliases.

## Definition of done

The unified implementation is complete when:

- all KG-family MCP servers use `kg_utils.mcp` for lifecycle and registration
- no repository manually constructs MCP JSON schemas or name dispatch tables
- PyCodeKG and TypeScriptKG share one implementation of common tools
- package servers contain only providers, configuration, domain callbacks,
  aliases, and thin entry points
- existing public commands and tool APIs remain compatible
- KGRAG can optionally act as the only configured MCP endpoint
- incompatible KG environments remain isolated
- text, structured, async, mutation, and image tools pass conformance tests
- tool manifests and server instructions cannot silently drift apart
- MCP dependency policy and major-version changes are managed centrally
