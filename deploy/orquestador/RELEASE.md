# Release: Workbench → imagen inmutable → Deployment

Convención de tags: `vX.Y.Z-oN` (ej. `v0.1.0-o1` = versión 0.1.0, Outcome 1). Un tag publicado **no se reutiliza**.

## Una sola vez (por namespace)
```bash
oc apply -f deploy/orquestador/buildconfig-imagestream.yaml
```

## Al cerrar un Outcome (desde la terminal del Workbench)
```bash
VERSION=v0.1.0-o1
git pull && test -z "$(git status --porcelain)"        # árbol limpio = build reproducible
git tag -a $VERSION -m "Outcome 1" && git push origin $VERSION

# 1) Build desde el commit (git archive de HEAD: ignora .venv, .env, cachés)
oc start-build orquestador-payworks --from-repo=. --commit=$VERSION --follow

# 2) Fija el tag versionado al digest recién construido (inmutable)
oc tag orquestador-payworks:build orquestador-payworks:$VERSION

# 3) Actualiza el Deployment (resuelve el tag a digest sha256)
oc set image deployment/orquestador-payworks \
  orquestador=orquestador-payworks:$VERSION --source=imagestreamtag
oc rollout status deployment/orquestador-payworks
```

## Rollback
```bash
oc set image deployment/orquestador-payworks \
  orquestador=orquestador-payworks:v0.0.9-o0 --source=imagestreamtag
```

Ver versiones disponibles: `oc get istag | grep orquestador-payworks`.

