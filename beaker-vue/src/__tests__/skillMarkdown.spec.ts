import { describe, it, expect } from 'vitest';
import {
    isRelativeHref,
    resolveResourceFromHref,
    type Integration,
} from '../util/integration';
import { renderMarkdown } from '../util/markdown';

const integration = {
    resources: {
        'r1': { resource_id: 'r1', resource_type: 'skill_file', relative_path: 'references/FILTERS.md' },
        'r2': { resource_id: 'r2', resource_type: 'skill_file', relative_path: 'references/CROSS-REPOSITORY.md' },
        'r3': { resource_id: 'r3', resource_type: 'skill_file', relative_path: 'assets/service_openapi.yaml' },
        'e1': { resource_id: 'e1', resource_type: 'skill_example', filename: 'find_cohort.md' },
        'i1': { resource_id: 'i1', resource_type: 'skill_instructions', content: '# hi' },
    },
} as unknown as Integration;

describe('isRelativeHref', () => {
    it('accepts relative paths', () => {
        expect(isRelativeHref('references/FILTERS.md')).toBe(true);
        expect(isRelativeHref('./FILTERS.md')).toBe(true);
        expect(isRelativeHref('../assets/service_openapi.yaml')).toBe(true);
    });

    it('rejects external, protocol-relative, mailto, and in-page links', () => {
        expect(isRelativeHref('https://example.com/x.md')).toBe(false);
        expect(isRelativeHref('http://example.com')).toBe(false);
        expect(isRelativeHref('//example.com/x.md')).toBe(false);
        expect(isRelativeHref('mailto:someone@example.com')).toBe(false);
        expect(isRelativeHref('#section')).toBe(false);
        expect(isRelativeHref('')).toBe(false);
    });
});

describe('resolveResourceFromHref', () => {
    it('resolves a skill-root link to a file resource', () => {
        expect(resolveResourceFromHref(integration, 'references/FILTERS.md')?.resource_id).toBe('r1');
    });

    it('resolves an examples/ link to an example resource', () => {
        expect(resolveResourceFromHref(integration, 'examples/find_cohort.md')?.resource_id).toBe('e1');
    });

    it('resolves sibling links against the linking file directory', () => {
        expect(resolveResourceFromHref(integration, 'CROSS-REPOSITORY.md', 'references')?.resource_id).toBe('r2');
    });

    it('resolves ../ traversal', () => {
        expect(resolveResourceFromHref(integration, '../assets/service_openapi.yaml', 'references')?.resource_id).toBe('r3');
    });

    it('ignores ./ segments, query strings, and fragments', () => {
        expect(resolveResourceFromHref(integration, './references/FILTERS.md')?.resource_id).toBe('r1');
        expect(resolveResourceFromHref(integration, 'references/FILTERS.md#operators')?.resource_id).toBe('r1');
        expect(resolveResourceFromHref(integration, 'references/FILTERS.md?x=1')?.resource_id).toBe('r1');
    });

    it('returns undefined for unknown paths and empty hrefs', () => {
        expect(resolveResourceFromHref(integration, 'auth.yaml')).toBeUndefined();
        expect(resolveResourceFromHref(integration, '')).toBeUndefined();
        expect(resolveResourceFromHref(undefined, 'references/FILTERS.md')).toBeUndefined();
    });
});

describe('renderMarkdown', () => {
    it('renders markdown to HTML', () => {
        const html = renderMarkdown('# Title\n\nSome **bold** text.');
        expect(html).toContain('<h1>');
        expect(html).toContain('<strong>bold</strong>');
    });

    it('strips script tags and event handlers from embedded HTML', () => {
        expect(renderMarkdown('hello <script>alert(1)</script>')).not.toContain('<script');
        const html = renderMarkdown('<img src="x" onerror="alert(1)">');
        expect(html).not.toContain('onerror');
    });

    it('neutralizes javascript: links but keeps normal ones', () => {
        expect(renderMarkdown('[x](javascript:alert(1))')).not.toContain('javascript:');
        expect(renderMarkdown('[x](https://example.com)')).toContain('href="https://example.com"');
        expect(renderMarkdown('[x](references/FILTERS.md)')).toContain('href="references/FILTERS.md"');
    });

    it('returns an empty string for empty input', () => {
        expect(renderMarkdown('')).toBe('');
        expect(renderMarkdown(undefined)).toBe('');
        expect(renderMarkdown(null)).toBe('');
    });
});
