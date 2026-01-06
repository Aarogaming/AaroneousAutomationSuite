# Summary
- [ ] Briefly describe the change

# Type of change
- [ ] Docs
- [ ] Tooling
- [ ] Tests
- [ ] Runtime
- [ ] UI

# Testing performed
```
dotnet build ProjectMaelstrom/ProjectMaelstrom.sln -c Debug
dotnet test ProjectMaelstrom/ProjectMaelstrom.sln -c Debug
dotnet run --project MaelstromToolkit/MaelstromToolkit.csproj -- selftest
```
- [ ] Ran the above commands
- [ ] Additional checks (list):

# Runtime guards impact
- [ ] Yes (If yes, update Runtime guards docs)
- [ ] No

# Checklist
- [ ] No secrets/credentials added
- [ ] Tests pass
- [ ] Docs updated if needed
