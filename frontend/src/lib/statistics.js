/**
 * GAIM Lab — 통계 계산 유틸리티
 * 
 * t-test, Cohen's d, 효과 크기 계산을 위한 모듈
 * Numerical Recipes 알고리즘 기반 정확한 p-value 계산
 */

// ─── 기본 통계 ───

/** 평균 */
export function mean(arr) {
    if (!arr || arr.length === 0) return 0
    return arr.reduce((a, b) => a + b, 0) / arr.length
}

/** 표본 표준편차 (n-1) */
export function sd(arr) {
    if (!arr || arr.length < 2) return 0
    const m = mean(arr)
    const variance = arr.reduce((sum, x) => sum + (x - m) ** 2, 0) / (arr.length - 1)
    return Math.sqrt(variance)
}


// ─── Welch's t-test ───

/**
 * 독립 표본 Welch's t-test
 * @param {number[]} a - 그룹 A 데이터
 * @param {number[]} b - 그룹 B 데이터
 * @returns {{ t: number, df: number, p: number, significant: boolean }}
 */
export function welchTTest(a, b) {
    const nA = a.length, nB = b.length
    if (nA < 2 || nB < 2) return { t: 0, df: 0, p: 1, significant: false }

    const mA = mean(a), mB = mean(b)
    const sA = sd(a), sB = sd(b)
    const varA = sA * sA, varB = sB * sB

    const se = Math.sqrt(varA / nA + varB / nB)
    if (se === 0) return { t: 0, df: nA + nB - 2, p: 1, significant: false }

    const t = (mA - mB) / se

    // Welch–Satterthwaite 자유도
    const num = (varA / nA + varB / nB) ** 2
    const den = (varA / nA) ** 2 / (nA - 1) + (varB / nB) ** 2 / (nB - 1)
    const df = den === 0 ? nA + nB - 2 : num / den

    // 양측 p-value
    const p = twoTailedPValue(Math.abs(t), df)

    return {
        t: +t.toFixed(3),
        df: +df.toFixed(1),
        p: +p.toFixed(4),
        significant: p < 0.05,
    }
}


// ─── Cohen's d ───

/**
 * Cohen's d (pooled standard deviation 사용)
 * @param {number[]} a - 그룹 A 데이터
 * @param {number[]} b - 그룹 B 데이터
 * @returns {number}
 */
export function cohensD(a, b) {
    const nA = a.length, nB = b.length
    if (nA < 2 || nB < 2) return 0
    const mA = mean(a), mB = mean(b)
    const sA = sd(a), sB = sd(b)
    const pooled = Math.sqrt(((nA - 1) * sA * sA + (nB - 1) * sB * sB) / (nA + nB - 2))
    if (pooled === 0) return 0
    return +((mA - mB) / pooled).toFixed(3)
}


/**
 * 효과 크기 판정
 * @param {number} d - Cohen's d 값
 * @returns {'small' | 'medium' | 'large'}
 */
export function effectSizeLabel(d) {
    const abs = Math.abs(d)
    if (abs >= 0.8) return 'large'
    if (abs >= 0.5) return 'medium'
    return 'small'
}


// ─── p-value 계산 (정확한 구현) ───

/**
 * t-분포의 양측 p-value
 * P(|T| > |t|) = I_{x}(df/2, 1/2)  where x = df / (df + t²)
 * 
 * @param {number} t - t 통계량 (절대값)
 * @param {number} df - 자유도
 * @returns {number} p-value
 */
function twoTailedPValue(t, df) {
    if (df <= 0) return 1
    if (t === 0) return 1
    const x = df / (df + t * t)
    return regularizedIncompleteBeta(df / 2, 0.5, x)
}


/**
 * 정규화 불완전 베타 함수 I_x(a, b)
 * Numerical Recipes 알고리즘 (continued fraction)
 * 
 * @param {number} a 
 * @param {number} b 
 * @param {number} x - 0 ≤ x ≤ 1
 * @returns {number}
 */
function regularizedIncompleteBeta(a, b, x) {
    if (x < 0 || x > 1) return 0
    if (x === 0) return 0
    if (x === 1) return 1

    // 로그 베타 계수
    const lnPrefactor = lnGamma(a + b) - lnGamma(a) - lnGamma(b)
        + a * Math.log(x) + b * Math.log(1 - x)

    // 수렴 성능을 위한 대칭 변환
    if (x < (a + 1) / (a + b + 2)) {
        return Math.exp(lnPrefactor) * betaContinuedFraction(a, b, x) / a
    } else {
        return 1 - Math.exp(lnPrefactor) * betaContinuedFraction(b, a, 1 - x) / b
    }
}


/**
 * 불완전 베타 함수의 연분수 전개 (Lentz's algorithm)
 * Numerical Recipes in C, 2nd Ed., §6.4
 */
function betaContinuedFraction(a, b, x) {
    const MAX_ITER = 200
    const EPS = 3.0e-12
    const FPMIN = 1.0e-30

    const qab = a + b
    const qap = a + 1
    const qam = a - 1

    let c = 1.0
    let d = 1.0 - qab * x / qap
    if (Math.abs(d) < FPMIN) d = FPMIN
    d = 1.0 / d
    let h = d

    for (let m = 1; m <= MAX_ITER; m++) {
        const m2 = 2 * m

        // Even step: d_{2m}
        let aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if (Math.abs(d) < FPMIN) d = FPMIN
        c = 1.0 + aa / c
        if (Math.abs(c) < FPMIN) c = FPMIN
        d = 1.0 / d
        h *= d * c

        // Odd step: d_{2m+1}
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if (Math.abs(d) < FPMIN) d = FPMIN
        c = 1.0 + aa / c
        if (Math.abs(c) < FPMIN) c = FPMIN
        d = 1.0 / d
        const del = d * c
        h *= del

        if (Math.abs(del - 1.0) <= EPS) break
    }

    return h
}


/**
 * 로그 감마 함수 — Lanczos 근사 (정밀도 ~15 자리)
 */
function lnGamma(z) {
    const g = 7
    const c = [
        0.99999999999980993,
        676.5203681218851,
        -1259.1392167224028,
        771.32342877765313,
        -176.61502916214059,
        12.507343278686905,
        -0.13857109526572012,
        9.9843695780195716e-6,
        1.5056327351493116e-7,
    ]

    if (z < 0.5) {
        return Math.log(Math.PI / Math.sin(Math.PI * z)) - lnGamma(1 - z)
    }

    z -= 1
    let x = c[0]
    for (let i = 1; i < g + 2; i++) {
        x += c[i] / (z + i)
    }
    const t = z + g + 0.5
    return 0.5 * Math.log(2 * Math.PI) + (z + 0.5) * Math.log(t) - t + Math.log(x)
}
