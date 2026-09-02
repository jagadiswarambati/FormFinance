# Project Structure

```text
apps/web/                 Next.js application shell
services/api/             FastAPI API and versioned health route
services/worker/          queue interface and worker entrypoint
packages/contracts/       shared boundary contracts
packages/policy/          policy interfaces
packages/ai-provider/     provider-neutral AI abstractions
packages/document-core/   document extraction/rendering interfaces
infra/                    future infrastructure-as-code home
docs/                     design records and developer documentation
tests/                    future cross-service fixtures
```

Domain implementations belong in their owning service. Packages expose interfaces and must not contain product business logic in Milestone 0.
