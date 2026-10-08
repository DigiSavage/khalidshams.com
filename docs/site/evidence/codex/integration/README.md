# Integrated drawings

Real page placements, captured after building `codex/illustrated-studio` on 2026-10-04.

- `home-intro`, `method-intro`, `learn-intro`: drawings now visible in page introductions.
- `method-map`, `method-ladder`, `method-gates`, `method-record`: drawings beside the reference they explain.
- `library-architecture`, `library-studios`, `library-systems`, `library-foundations`, `library-routes`: all distinct vignette drawings and both studio previews on the public library page.

Each has 390 and 1920 versions in light and dark: 48 JPEGs. `checks.json` records the 213 integration assertions across the full viewport matrix, including a 200 percent zoom equivalent and reduced motion. Element captures hide sticky site navigation only while taking the screenshot so that long sections remain unobscured. Interaction checks run with normal navigation.

Reproduce after serving a fresh build on port 8767:

```sh
.venv/bin/python tests/site/run_cached.py tests/site/integration_check.py http://localhost:8767 docs/site/evidence/codex/integration
```

The eight missing raster studies are not part of these screenshots. All illustrated scenes here come from the repository's SVG generators.
