/**
 * statistics.js 단위 테스트
 * 
 * 알려진 값과 비교하여 통계 함수의 정확성을 검증합니다.
 */

import { describe, it, expect } from 'vitest'
import { mean, sd, welchTTest, cohensD, effectSizeLabel } from '../lib/statistics'

describe('Statistics Module', () => {
    describe('mean', () => {
        it('빈 배열은 0을 반환', () => {
            expect(mean([])).toBe(0)
        })
        it('단일 값', () => {
            expect(mean([5])).toBe(5)
        })
        it('여러 값의 평균', () => {
            expect(mean([2, 4, 6, 8])).toBe(5)
        })
    })

    describe('sd (표본 표준편차)', () => {
        it('단일 값은 0을 반환', () => {
            expect(sd([5])).toBe(0)
        })
        it('동일 값은 0을 반환', () => {
            expect(sd([3, 3, 3, 3])).toBe(0)
        })
        it('알려진 값 검증 [2, 4, 6, 8]', () => {
            // 표본 분산 = 20/3, 표준편차 ≈ 2.582
            const result = sd([2, 4, 6, 8])
            expect(result).toBeCloseTo(2.582, 2)
        })
    })

    describe('welchTTest', () => {
        it('동일한 그룹은 t=0, p=1', () => {
            const result = welchTTest([5, 5, 5], [5, 5, 5])
            expect(result.t).toBe(0)
            expect(result.p).toBe(1)
            expect(result.significant).toBe(false)
        })

        it('크게 다른 두 그룹은 유의', () => {
            const a = [90, 92, 88, 95, 91]
            const b = [60, 58, 62, 55, 59]
            const result = welchTTest(a, b)
            expect(result.t).toBeGreaterThan(0)
            expect(result.p).toBeLessThan(0.001)
            expect(result.significant).toBe(true)
        })

        it('비슷한 두 그룹은 비유의', () => {
            const a = [80, 82, 78, 85, 81]
            const b = [79, 83, 77, 84, 80]
            const result = welchTTest(a, b)
            expect(result.significant).toBe(false)
            expect(result.p).toBeGreaterThan(0.05)
        })

        it('자유도(df)가 계산', () => {
            const a = [10, 20, 30, 40, 50]
            const b = [15, 25, 35]
            const result = welchTTest(a, b)
            expect(result.df).toBeGreaterThan(0)
        })

        it('알려진 t-test 결과와 비교', () => {
            // 두 그룹: A=[85, 90, 78, 92, 88], B=[70, 75, 68, 72, 74]
            // Welch's t-test: t ≈ 5.37, p < 0.01
            const a = [85, 90, 78, 92, 88]
            const b = [70, 75, 68, 72, 74]
            const result = welchTTest(a, b)
            expect(result.t).toBeCloseTo(5.37, 1)
            expect(result.p).toBeLessThan(0.01)
            expect(result.significant).toBe(true)
        })
    })

    describe('cohensD', () => {
        it('동일한 그룹은 d=0', () => {
            expect(cohensD([5, 5, 5], [5, 5, 5])).toBe(0)
        })

        it('large 효과 크기', () => {
            const a = [90, 92, 88, 95, 91]
            const b = [60, 58, 62, 55, 59]
            const d = cohensD(a, b)
            expect(Math.abs(d)).toBeGreaterThan(0.8)
        })
    })

    describe('effectSizeLabel', () => {
        it('small: |d| < 0.5', () => {
            expect(effectSizeLabel(0.3)).toBe('small')
            expect(effectSizeLabel(-0.2)).toBe('small')
        })
        it('medium: 0.5 ≤ |d| < 0.8', () => {
            expect(effectSizeLabel(0.6)).toBe('medium')
            expect(effectSizeLabel(-0.7)).toBe('medium')
        })
        it('large: |d| ≥ 0.8', () => {
            expect(effectSizeLabel(1.2)).toBe('large')
            expect(effectSizeLabel(-0.9)).toBe('large')
        })
    })
})
