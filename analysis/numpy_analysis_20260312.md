> **Analysis Report Metadata**  
> - **Generated:** 2026-03-12T01:52:26Z  
> - **Version:** pycode-kg 0.7.1  
> - **Commit:** b981a5f (main)  
> - **Platform:** Darwin arm64 | Python 3.12.10  
> - **Graph:** 126666 nodes · 252449 edges (14475 meaningful)  
> - **Included directories:** all  
> - **Elapsed time:** 6m 4s  

# numpy Analysis

**Generated:** 2026-03-12 01:52:26 UTC

---

## 📊 Executive Summary

This report provides a comprehensive architectural analysis of the **numpy** repository using PyCodeKG's knowledge graph. The analysis covers complexity hotspots, module coupling, key call chains, and code quality signals to guide refactoring and architecture decisions.

| Overall Quality | Grade | Score |
|----------------|-------|-------|
| 🔴 **Critical** | **F** | 35 / 100 |

---

## 📈 Baseline Metrics

| Metric | Value |
|--------|-------|
| **Total Nodes** | 126666 |
| **Total Edges** | 252449 |
| **Modules** | 491 (of 491 total) |
| **Functions** | 3581 |
| **Classes** | 1813 |
| **Methods** | 8590 |

### Edge Distribution

| Relationship Type | Count |
|-------------------|-------|
| CALLS | 47639 |
| CONTAINS | 13984 |
| IMPORTS | 4164 |
| ATTR_ACCESS | 40595 |
| INHERITS | 656 |

---

## 🔥 Fan-In Ranking

Most-called functions are potential bottlenecks or core functionality. These functions are heavily depended upon across the codebase.

| # | Function | Module | Callers |
|---|----------|--------|---------|
| 1 | `array()` | numpy/_core/defchararray.py | **2845** |
| 2 | `dtype()` | numpy/ma/core.py | **708** |
| 3 | `asarray()` | numpy/_core/defchararray.py | **217** |
| 4 | `asarray()` | numpy/ma/core.py | **211** |
| 5 | `asanyarray()` | numpy/ma/core.py | **110** |
| 6 | `filled()` | numpy/ma/core.py | **87** |
| 7 | `getmask()` | numpy/ma/core.py | **64** |
| 8 | `filled()` | numpy/ma/core.py | **56** |
| 9 | `unique()` | numpy/lib/_arraysetops_impl.py | **49** |
| 10 | `unique()` | numpy/ma/extras.py | **49** |
| 11 | `as_series()` | numpy/polynomial/polyutils.py | **47** |
| 12 | `isscalar()` | numpy/f2py/auxfuncs.py | **45** |
| 13 | `shape()` | numpy/ma/core.py | **44** |
| 14 | `close()` | numpy/lib/_npyio_impl.py | **43** |
| 15 | `__init__()` | tools/swig/test/testFlat.py | **42** |


**Insight:** Functions with high fan-in are either core APIs or bottlenecks. Review these for:
- Thread safety and performance
- Clear documentation and contracts
- Potential for breaking changes

---

## 🔗 High Fan-Out Functions (Orchestrators)

Functions that call many others may indicate complex orchestration logic or poor separation of concerns.

✓ No extreme high fan-out functions detected. Well-balanced architecture.

---

## 📦 Module Architecture

Top modules by dependency coupling and cohesion (showing up to 10 with activity).
Cohesion = incoming / (incoming + outgoing + 1); higher = more internally focused.

| Module | Functions | Classes | Incoming | Outgoing | Cohesion |
|--------|-----------|---------|----------|----------|----------|
| `numpy/_core/tests/test_multiarray.py` | 85 | 148 | 3 | 10 | 0.71 |
| `numpy/_core/tests/test_umath.py` | 52 | 96 | 2 | 6 | 0.67 |
| `numpy/lib/tests/test_function_base.py` | 26 | 54 | 0 | 12 | 0.92 |
| `numpy/ma/tests/test_core.py` | 30 | 24 | 0 | 30 | 0.97 |
| `numpy/_core/tests/test_numeric.py` | 5 | 49 | 4 | 8 | 0.62 |
| `numpy/_core/tests/test_regression.py` | 11 | 14 | 0 | 11 | 0.92 |
| `numpy/ma/core.py` | 105 | 18 | 75 | 14 | 0.16 |
| `numpy/_core/tests/test_ufunc.py` | 28 | 21 | 3 | 6 | 0.60 |
| `numpy/random/tests/test_generator_mt19937.py` | 14 | 12 | 0 | 4 | 0.80 |
| `numpy/lib/tests/test_io.py` | 15 | 14 | 5 | 7 | 0.54 |

---

## 🔗 Key Call Chains

Deepest call chains in the codebase.

**Chain 1** (depth: 5)

```
_get_dtype_of → dtype → make_mask_descr → _replace_dtype_fields → _replace_dtype_fields_recursive
```

**Chain 2** (depth: 4)

```
__mul__ → asarray → array → chararray
```

**Chain 3** (depth: 5)

```
compressed → asanyarray → dtype → make_mask_descr → _replace_dtype_fields
```

---

## 🔓 Public API Surface

Identified public APIs (module-level functions with high usage).

| Function | Module | Fan-In | Type |
|----------|--------|--------|------|
| `array()` | numpy/ma/core.py | 3092 | function |
| `array()` | numpy/_core/defchararray.py | 2845 | function |
| `array()` | numpy/_core/records.py | 2844 | function |
| `dtype()` | numpy/_core/tests/test_stringdtype.py | 668 | function |
| `reshape()` | numpy/ma/core.py | 582 | function |
| `zeros()` | numpy/matlib.py | 549 | function |
| `reshape()` | numpy/_core/fromnumeric.py | 548 | function |
| `ones()` | numpy/_core/numeric.py | 508 | function |
| `ones()` | numpy/matlib.py | 497 | function |
| `astype()` | numpy/_core/numeric.py | 487 | function |
---

## 📝 Docstring Coverage

Docstring coverage directly determines semantic retrieval quality. Nodes without
docstrings embed only structured identifiers (`KIND/NAME/QUALNAME/MODULE`), where
keyword search is as effective as vector embeddings. The semantic model earns its
value only when a docstring is present.

| Kind | Documented | Total | Coverage |
|------|-----------|-------|----------|
| `function` | 1342 | 3581 | 🔴 37.5% |
| `method` | 809 | 8590 | 🔴 9.4% |
| `class` | 258 | 1813 | 🔴 14.2% |
| `module` | 195 | 491 | 🔴 39.7% |
| **total** | **2604** | **14475** | **🔴 18.0%** |

> **Recommendation:** 11871 nodes lack docstrings. Prioritize documenting high-fan-in functions and public API surface first — these have the highest impact on query accuracy.

---

## 🏆 Structural Importance Ranking (SIR)

Weighted PageRank aggregated by module — reveals architectural spine. Cross-module edges boosted 1.5×; private symbols penalized 0.85×. Node-level detail: `pycodekg centrality --top 25`

| Rank | Score | Members | Module |
|------|-------|---------|--------|
| 1 | 0.146052 | 280 | `numpy/ma/core.py` |
| 2 | 0.042109 | 70 | `numpy/_core/defchararray.py` |
| 3 | 0.040892 | 80 | `numpy/testing/_private/utils.py` |
| 4 | 0.030072 | 974 | `numpy/_core/tests/test_multiarray.py` |
| 5 | 0.026878 | 8 | `numpy/_core/overrides.py` |
| 6 | 0.025697 | 18 | `numpy/ma/testutils.py` |
| 7 | 0.023614 | 6 | `numpy/_utils/__init__.py` |
| 8 | 0.023231 | 91 | `numpy/_core/fromnumeric.py` |
| 9 | 0.019957 | 17 | `benchmarks/benchmarks/bench_overrides.py` |
| 10 | 0.018568 | 29 | `numpy/_core/records.py` |
| 11 | 0.017776 | 30 | `numpy/ma/mrecords.py` |
| 12 | 0.016807 | 51 | `numpy/_core/strings.py` |
| 13 | 0.016139 | 48 | `numpy/lib/_npyio_impl.py` |
| 14 | 0.015944 | 439 | `numpy/_core/tests/test_umath.py` |
| 15 | 0.015173 | 38 | `numpy/matrixlib/defmatrix.py` |



---

## ⚠️  Code Quality Issues

- 🔴 Low docstring coverage (18.0%) — semantic query quality will be poor; embedding undocumented nodes yields only structured identifiers, not NL-searchable text. Prioritize docstrings on high-fan-in functions first.
- ⚠️  8 orphaned functions found (`public`, `local`, `test_unused_converter`, `test_unused_converter`, `test_deprecated`, `test_testSingleElementSubscript`, `TestArrayMethods`, `base_version`) — consider archiving or documenting
- ⚠️  Diamond inheritance detected: `D`, `CondCases`, `DetCases`, `EigCases`, `EigvalsCases`, `InvCases`, `LstsqCases`, `PinvCases`, `PinvHermitianCases`, `SVDCases`, `SVDHermitianCases`, `SolveCases`, `TestEighCases`, `TestEigvalshCases`, `TestNormDouble`, `TestNormInt64`, `TestNormSingle`, `_TestNorm`, `MSubArray`, `MMatrix`, `TestCondMatrix`, `TestDetMatrix`, `TestEigMatrix`, `TestEigvalsMatrix`, `TestInvMatrix`, `TestLstsqMatrix`, `TestNormDoubleMatrix`, `TestNormInt64Matrix`, `TestNormSingleMatrix`, `TestPinvMatrix`, `TestSVDMatrix`, `TestSolveMatrix` — verify MRO is intentional (C3 linearisation)
- ⚠️  Deep inheritance hierarchy (max depth 6) — consider flattening via composition

---

## ✅ Architectural Strengths

- ✓ Well-structured with 15 core functions identified
- ✓ No god objects or god functions detected

---

## 💡 Recommendations

### Immediate Actions
1. **Improve docstring coverage** — 11871 nodes lack docstrings; prioritize high-fan-in functions and public APIs first for maximum semantic retrieval gain
2. **Remove or archive orphaned functions** — `public`, `local`, `test_unused_converter`, `test_unused_converter`, `test_deprecated` (and 3 more) have zero callers and add maintenance burden

### Medium-term Refactoring
1. **Harden high fan-in functions** — `array`, `dtype`, `asarray` are widely depended upon; review for thread safety, clear contracts, and stable interfaces
2. **Reduce module coupling** — consider splitting tightly coupled modules or introducing interface boundaries
3. **Add tests for key call chains** — the identified call chains represent well-traveled execution paths that benefit most from regression coverage

### Long-term Architecture
1. **Version and stabilize the public API** — document breaking-change policies for `array`, `array`, `array`
2. **Enforce layer boundaries** — add linting or CI checks to prevent unexpected cross-module dependencies as the codebase grows
3. **Monitor hot paths** — instrument the high fan-in functions identified here to catch performance regressions early

---

## 🧬 Inheritance Hierarchy

**656** INHERITS edges across **716** classes. Max depth: **6**.

| Class | Module | Depth | Parents | Children |
|-------|--------|-------|---------|----------|
| `_8Bit` | numpy/_typing/_nbit_base.py | 6 | 1 | 0 |
| `_16Bit` | numpy/_typing/_nbit_base.py | 5 | 1 | 1 |
| `_32Bit` | numpy/_typing/_nbit_base.py | 4 | 1 | 1 |
| `BinaryFPSpecial` | benchmarks/benchmarks/bench_ufunc_strides.py | 3 | 1 | 0 |
| `UnaryFPSpecial` | benchmarks/benchmarks/bench_ufunc_strides.py | 3 | 1 | 0 |
| `D` | numpy/_core/tests/test_scalarinherit.py | 3 | 2 | 0 |
| `_64Bit` | numpy/_typing/_nbit_base.py | 3 | 1 | 1 |
| `TestCond` | numpy/linalg/tests/test_linalg.py | 3 | 1 | 0 |
| `TestDet` | numpy/linalg/tests/test_linalg.py | 3 | 1 | 0 |
| `TestEig` | numpy/linalg/tests/test_linalg.py | 3 | 1 | 0 |
| `TestEigvals` | numpy/linalg/tests/test_linalg.py | 3 | 1 | 0 |
| `TestInv` | numpy/linalg/tests/test_linalg.py | 3 | 1 | 0 |
| `TestLstsq` | numpy/linalg/tests/test_linalg.py | 3 | 1 | 0 |
| `TestNormDouble` | numpy/linalg/tests/test_linalg.py | 3 | 2 | 0 |
| `TestNormInt64` | numpy/linalg/tests/test_linalg.py | 3 | 2 | 0 |
| `TestNormSingle` | numpy/linalg/tests/test_linalg.py | 3 | 2 | 0 |
| `TestPinv` | numpy/linalg/tests/test_linalg.py | 3 | 1 | 0 |
| `TestPinvHermitian` | numpy/linalg/tests/test_linalg.py | 3 | 1 | 0 |
| `TestSVD` | numpy/linalg/tests/test_linalg.py | 3 | 2 | 0 |
| `TestSVDHermitian` | numpy/linalg/tests/test_linalg.py | 3 | 2 | 0 |

### Multiple Inheritance (38 classes)

- `B` (numpy/_core/tests/test_scalarinherit.py) inherits from `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `np.float64`
- `B0` (numpy/_core/tests/test_scalarinherit.py) inherits from `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `A`, `np.float64`
- `B1` (numpy/_core/tests/test_scalarinherit.py) inherits from `HasNew`, `np.float64`
- `D` (numpy/_core/tests/test_scalarinherit.py) inherits from `B`, `B`, `B`, `B`, `B`, `B`, `B`, `B`, `B`, `B`, `B`, `B`, `C`, `C`, `C`, `C`, `C`, `C`, `C`, `C`, `C`, `C`, `C`, `C`, `C`, `C`
- `AxisError` (numpy/exceptions.py) inherits from `IndexError`, `ValueError`
- `CondCases` (numpy/linalg/tests/test_linalg.py) inherits from `LinalgGeneralizedSquareTestCase`, `LinalgSquareTestCase`
- `DetCases` (numpy/linalg/tests/test_linalg.py) inherits from `LinalgGeneralizedSquareTestCase`, `LinalgSquareTestCase`
- `EigCases` (numpy/linalg/tests/test_linalg.py) inherits from `LinalgGeneralizedSquareTestCase`, `LinalgSquareTestCase`
- `EigvalsCases` (numpy/linalg/tests/test_linalg.py) inherits from `LinalgGeneralizedSquareTestCase`, `LinalgSquareTestCase`
- `InvCases` (numpy/linalg/tests/test_linalg.py) inherits from `LinalgGeneralizedSquareTestCase`, `LinalgSquareTestCase`
- `LstsqCases` (numpy/linalg/tests/test_linalg.py) inherits from `LinalgNonsquareTestCase`, `LinalgSquareTestCase`
- `PinvCases` (numpy/linalg/tests/test_linalg.py) inherits from `LinalgGeneralizedNonsquareTestCase`, `LinalgGeneralizedSquareTestCase`, `LinalgNonsquareTestCase`, `LinalgSquareTestCase`
- `PinvHermitianCases` (numpy/linalg/tests/test_linalg.py) inherits from `HermitianGeneralizedTestCase`, `HermitianTestCase`
- `SVDCases` (numpy/linalg/tests/test_linalg.py) inherits from `LinalgGeneralizedSquareTestCase`, `LinalgSquareTestCase`
- `SVDHermitianCases` (numpy/linalg/tests/test_linalg.py) inherits from `HermitianGeneralizedTestCase`, `HermitianTestCase`
- `SolveCases` (numpy/linalg/tests/test_linalg.py) inherits from `LinalgGeneralizedSquareTestCase`, `LinalgSquareTestCase`
- `TestEighCases` (numpy/linalg/tests/test_linalg.py) inherits from `HermitianGeneralizedTestCase`, `HermitianTestCase`
- `TestEigvalshCases` (numpy/linalg/tests/test_linalg.py) inherits from `HermitianGeneralizedTestCase`, `HermitianTestCase`
- `TestNormDouble` (numpy/linalg/tests/test_linalg.py) inherits from `_TestNorm`, `_TestNormDoubleBase`
- `TestNormInt64` (numpy/linalg/tests/test_linalg.py) inherits from `_TestNorm`, `_TestNormInt64Base`
- `TestNormSingle` (numpy/linalg/tests/test_linalg.py) inherits from `_TestNorm`, `_TestNormSingleBase`
- `TestSVD` (numpy/linalg/tests/test_linalg.py) inherits from `SVDBaseTests`, `SVDCases`
- `TestSVDHermitian` (numpy/linalg/tests/test_linalg.py) inherits from `SVDBaseTests`, `SVDHermitianCases`
- `_TestNorm` (numpy/linalg/tests/test_linalg.py) inherits from `_TestNorm2D`, `_TestNormGeneral`
- `MSubArray` (numpy/ma/tests/test_subclassing.py) inherits from `MaskedArray`, `SubArray`
- `MMatrix` (numpy/matrixlib/tests/test_masked_matrix.py) inherits from `MaskedArray`, `matrix`
- `TestCondMatrix` (numpy/matrixlib/tests/test_matrix_linalg.py) inherits from `CondCases`, `MatrixTestCase`, `MatrixTestCase`
- `TestDetMatrix` (numpy/matrixlib/tests/test_matrix_linalg.py) inherits from `DetCases`, `MatrixTestCase`, `MatrixTestCase`
- `TestEigMatrix` (numpy/matrixlib/tests/test_matrix_linalg.py) inherits from `EigCases`, `MatrixTestCase`, `MatrixTestCase`
- `TestEigvalsMatrix` (numpy/matrixlib/tests/test_matrix_linalg.py) inherits from `EigvalsCases`, `MatrixTestCase`, `MatrixTestCase`
- `TestInvMatrix` (numpy/matrixlib/tests/test_matrix_linalg.py) inherits from `InvCases`, `MatrixTestCase`, `MatrixTestCase`
- `TestLstsqMatrix` (numpy/matrixlib/tests/test_matrix_linalg.py) inherits from `LstsqCases`, `MatrixTestCase`, `MatrixTestCase`
- `TestNormDoubleMatrix` (numpy/matrixlib/tests/test_matrix_linalg.py) inherits from `_TestNorm2DMatrix`, `_TestNormDoubleBase`
- `TestNormInt64Matrix` (numpy/matrixlib/tests/test_matrix_linalg.py) inherits from `_TestNorm2DMatrix`, `_TestNormInt64Base`
- `TestNormSingleMatrix` (numpy/matrixlib/tests/test_matrix_linalg.py) inherits from `_TestNorm2DMatrix`, `_TestNormSingleBase`
- `TestPinvMatrix` (numpy/matrixlib/tests/test_matrix_linalg.py) inherits from `MatrixTestCase`, `MatrixTestCase`, `PinvCases`
- `TestSVDMatrix` (numpy/matrixlib/tests/test_matrix_linalg.py) inherits from `MatrixTestCase`, `MatrixTestCase`, `SVDCases`
- `TestSolveMatrix` (numpy/matrixlib/tests/test_matrix_linalg.py) inherits from `MatrixTestCase`, `MatrixTestCase`, `SolveCases`

### ⚠️ Diamond Patterns (32 detected)

- `D` (numpy/_core/tests/test_scalarinherit.py) — common ancestor(s): `B`
- `CondCases` (numpy/linalg/tests/test_linalg.py) — common ancestor(s): `LinalgTestCase`
- `DetCases` (numpy/linalg/tests/test_linalg.py) — common ancestor(s): `LinalgTestCase`
- `EigCases` (numpy/linalg/tests/test_linalg.py) — common ancestor(s): `LinalgTestCase`
- `EigvalsCases` (numpy/linalg/tests/test_linalg.py) — common ancestor(s): `LinalgTestCase`
- `InvCases` (numpy/linalg/tests/test_linalg.py) — common ancestor(s): `LinalgTestCase`
- `LstsqCases` (numpy/linalg/tests/test_linalg.py) — common ancestor(s): `LinalgTestCase`
- `PinvCases` (numpy/linalg/tests/test_linalg.py) — common ancestor(s): `LinalgTestCase`
- `PinvHermitianCases` (numpy/linalg/tests/test_linalg.py) — common ancestor(s): `LinalgTestCase`
- `SVDCases` (numpy/linalg/tests/test_linalg.py) — common ancestor(s): `LinalgTestCase`
- `SVDHermitianCases` (numpy/linalg/tests/test_linalg.py) — common ancestor(s): `LinalgTestCase`
- `SolveCases` (numpy/linalg/tests/test_linalg.py) — common ancestor(s): `LinalgTestCase`
- `TestEighCases` (numpy/linalg/tests/test_linalg.py) — common ancestor(s): `LinalgTestCase`
- `TestEigvalshCases` (numpy/linalg/tests/test_linalg.py) — common ancestor(s): `LinalgTestCase`
- `TestNormDouble` (numpy/linalg/tests/test_linalg.py) — common ancestor(s): `_TestNormBase`
- `TestNormInt64` (numpy/linalg/tests/test_linalg.py) — common ancestor(s): `_TestNormBase`
- `TestNormSingle` (numpy/linalg/tests/test_linalg.py) — common ancestor(s): `_TestNormBase`
- `_TestNorm` (numpy/linalg/tests/test_linalg.py) — common ancestor(s): `_TestNormBase`
- `MSubArray` (numpy/ma/tests/test_subclassing.py) — common ancestor(s): `ndarray`
- `MMatrix` (numpy/matrixlib/tests/test_masked_matrix.py) — common ancestor(s): `ndarray`
- `TestCondMatrix` (numpy/matrixlib/tests/test_matrix_linalg.py) — common ancestor(s): `LinalgTestCase`
- `TestDetMatrix` (numpy/matrixlib/tests/test_matrix_linalg.py) — common ancestor(s): `LinalgTestCase`
- `TestEigMatrix` (numpy/matrixlib/tests/test_matrix_linalg.py) — common ancestor(s): `LinalgTestCase`
- `TestEigvalsMatrix` (numpy/matrixlib/tests/test_matrix_linalg.py) — common ancestor(s): `LinalgTestCase`
- `TestInvMatrix` (numpy/matrixlib/tests/test_matrix_linalg.py) — common ancestor(s): `LinalgTestCase`
- `TestLstsqMatrix` (numpy/matrixlib/tests/test_matrix_linalg.py) — common ancestor(s): `LinalgTestCase`
- `TestNormDoubleMatrix` (numpy/matrixlib/tests/test_matrix_linalg.py) — common ancestor(s): `_TestNormBase`
- `TestNormInt64Matrix` (numpy/matrixlib/tests/test_matrix_linalg.py) — common ancestor(s): `_TestNormBase`
- `TestNormSingleMatrix` (numpy/matrixlib/tests/test_matrix_linalg.py) — common ancestor(s): `_TestNormBase`
- `TestPinvMatrix` (numpy/matrixlib/tests/test_matrix_linalg.py) — common ancestor(s): `LinalgTestCase`
- `TestSVDMatrix` (numpy/matrixlib/tests/test_matrix_linalg.py) — common ancestor(s): `LinalgTestCase`
- `TestSolveMatrix` (numpy/matrixlib/tests/test_matrix_linalg.py) — common ancestor(s): `LinalgTestCase`


---

## 📸 Snapshot History

No snapshots found. Run `pycodekg snapshot save <version>` to capture one.


---

## 📋 Appendix: Orphaned Code

Functions with zero callers (potential dead code):

| Function | Module | Lines |
|----------|--------|-------|
| `TestArrayMethods()` | numpy/ma/tests/test_old_ma.py | 86 |
| `test_unused_converter()` | numpy/lib/tests/test_io.py | 11 |
| `test_unused_converter()` | numpy/lib/tests/test_io.py | 10 |
| `test_testSingleElementSubscript()` | numpy/ma/tests/test_old_ma.py | 5 |
| `test_deprecated()` | numpy/_core/tests/test_array_coercion.py | 4 |
| `public()` | numpy/_utils/_pep440.py | 1 |
| `local()` | numpy/_utils/_pep440.py | 1 |
| `base_version()` | numpy/_utils/_pep440.py | 1 |
---

## 📐 CodeRank — Global Structural Importance

Weighted PageRank over CALLS + IMPORTS + INHERITS edges (test paths excluded). Scores are normalized to sum to 1.0. This ranking seeds Phase 2 fan-in discovery and Phase 15 concern queries.

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.000413 | method | `container._rc` | numpy/lib/_user_array_impl.py |
| 2 | 0.000409 | method | `MaskedArray.dtype` | numpy/ma/core.py |
| 3 | 0.000357 | function | `isexternal` | numpy/f2py/auxfuncs.py |
| 4 | 0.000348 | class | `Expr` | numpy/f2py/symbolic.py |
| 5 | 0.000288 | method | `MaskedArray.shape` | numpy/ma/core.py |
| 6 | 0.000257 | method | `mvoid._data` | numpy/ma/core.py |
| 7 | 0.000248 | function | `getmask` | numpy/ma/core.py |
| 8 | 0.000228 | function | `_wrapfunc` | numpy/_core/fromnumeric.py |
| 9 | 0.000227 | method | `SuperTensorTestCase.__init__` | tools/swig/test/testSuperTensor.py |
| 10 | 0.000227 | method | `FortranTestCase.__init__` | tools/swig/test/testFortran.py |
| 11 | 0.000227 | method | `VectorTestCase.__init__` | tools/swig/test/testVector.py |
| 12 | 0.000227 | method | `MatrixTestCase.__init__` | tools/swig/test/testMatrix.py |
| 13 | 0.000227 | method | `FlatTestCase.__init__` | tools/swig/test/testFlat.py |
| 14 | 0.000219 | class | `LinAlgError` | numpy/linalg/_linalg.py |
| 15 | 0.000210 | function | `isarray` | numpy/f2py/auxfuncs.py |
| 16 | 0.000192 | function | `asarray` | numpy/_core/defchararray.py |
| 17 | 0.000188 | method | `ABCPolyBase.domain` | numpy/polynomial/_polybase.py |
| 18 | 0.000179 | method | `ABCPolyBase.window` | numpy/polynomial/_polybase.py |
| 19 | 0.000169 | method | `TensorTestCase.__init__` | tools/swig/test/testTensor.py |
| 20 | 0.000164 | function | `make_mask_descr` | numpy/ma/core.py |

---

## 🔎 Concern-Based Hybrid Ranking

Top structurally-dominant nodes per architectural concern (0.60 × semantic + 0.25 × CodeRank + 0.15 × graph proximity).

### Error Handling Exception Recovery

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.7481 | method | `_ArrayMemoryError.__str__` | numpy/_core/_exceptions.py |
| 2 | 0.7437 | method | `_UFuncInputCastingError.__str__` | numpy/_core/_exceptions.py |
| 3 | 0.6918 | class | `ConverterError` | numpy/lib/_iotools.py |
| 4 | 0.6864 | class | `ConverterLockError` | numpy/lib/_iotools.py |
| 5 | 0.685 | class | `KnownFailureException` | numpy/testing/_private/utils.py |

### Configuration Loading Initialization Setup

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.75 | method | `LoadtxtCSVDateTime.setup` | benchmarks/benchmarks/bench_io.py |
| 2 | 0.7473 | method | `LoadtxtCSVComments.setup` | benchmarks/benchmarks/bench_io.py |
| 3 | 0.7456 | method | `LoadtxtUseColsCSV.setup` | benchmarks/benchmarks/bench_io.py |
| 4 | 0.7438 | method | `LoadNpyOverhead.setup` | benchmarks/benchmarks/bench_io.py |
| 5 | 0.7414 | method | `CustomInplace.setup` | benchmarks/benchmarks/bench_ufunc.py |

### Data Persistence Storage Database

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.7505 | method | `DataSource._cache` | numpy/lib/_datasource.py |
| 2 | 0.75 | function | `get_data` | benchmarks/benchmarks/common.py |
| 4 | 0.065 | method | `container._rc` | numpy/lib/_user_array_impl.py |

### Query Search Retrieval Semantic

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.7423 | method | `SearchSorted.time_searchsorted` | benchmarks/benchmarks/bench_searchsorted.py |
| 2 | 0.7223 | function | `_search_sorted_inclusive` | numpy/lib/_histograms_impl.py |
| 3 | 0.7211 | function | `joinseq` | numpy/_utils/_inspect.py |
| 4 | 0.69 | class | `SearchSorted` | benchmarks/benchmarks/bench_searchsorted.py |
| 5 | 0.6642 | class | `Indexing` | benchmarks/benchmarks/bench_ma.py |

### Graph Traversal Node Edge

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.7509 | function | `_get_edges` | numpy/lib/_arraypad_impl.py |
| 2 | 0.7495 | function | `notmasked_edges` | numpy/ma/extras.py |
| 3 | 0.7471 | function | `block` | numpy/_core/shape_base.py |
| 4 | 0.7461 | function | `_block` | numpy/_core/shape_base.py |
| 5 | 0.7445 | function | `put_along_axis` | numpy/lib/_shape_base_impl.py |



---

*Report generated by PyCodeKG Thorough Analysis Tool — analysis completed in 6.1m*
