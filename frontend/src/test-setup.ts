import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'
afterEach(() => { cleanup(); vi.restoreAllMocks() })
HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', '') }
window.scrollTo = vi.fn()
