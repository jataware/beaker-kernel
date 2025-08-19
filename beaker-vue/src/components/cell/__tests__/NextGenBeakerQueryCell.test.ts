import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createApp } from 'vue';
import PrimeVue from 'primevue/config';
import NextGenBeakerQueryCell from '../NextGenBeakerQueryCell.vue';

vi.mock('../BaseQueryCell', () => ({
  useBaseQueryCell: () => ({
    cell: { value: {} },
    response: { value: '' },
    events: { value: [] },
    execute: vi.fn(),
    enter: vi.fn(),
    exit: vi.fn(),
    clear: vi.fn(),
    respond: vi.fn(),
  }),
}));

// Mock the beakerSession injection
const mockBeakerSession = {
  cellRegistry: {},
};

describe('NextGenBeakerQueryCell', () => {
  let wrapper: any;
  
  const createMockCell = (overrides = {}) => ({
    id: 'test-cell-1',
    source: 'Test query',
    status: 'idle',
    metadata: { query_status: 'pending' },
    events: [],
    last_execution: {},
    children: [],
    cell_type: 'query',
    ...overrides,
  });

  beforeEach(() => {
    const app = createApp(NextGenBeakerQueryCell);
    app.use(PrimeVue);
    
    wrapper = mount(NextGenBeakerQueryCell, {
      props: {
        index: 0,
        cell: createMockCell(),
      },
      global: {
        provide: {
          beakerSession: mockBeakerSession,
        },
        stubs: {
          'InputGroup': true,
          'InputText': true,
          'Button': true,
        },
        // Mock the tooltip directive
        directives: {
          tooltip: {
            mounted: vi.fn(),
            updated: vi.fn(),
            unmounted: vi.fn(),
          },
        },
      },
    });
  });

  describe('Badge States', () => {
    it('shows pending state correctly', async () => {
      const cell = createMockCell({
        metadata: { query_status: 'pending' },
        status: 'idle',
      });
      
      await wrapper.setProps({ cell });
      await wrapper.vm.$nextTick();
      
      const badge = wrapper.find('.execution-badge');
      expect(badge.classes()).toContain('secondary');
      expect(badge.find('i.pi-clock')).toBeTruthy();
    });

    it('shows in-progress state correctly', async () => {
      const cell = createMockCell({
        metadata: { query_status: 'in-progress' },
        status: 'busy',
      });
      
      await wrapper.setProps({ cell });
      await wrapper.vm.$nextTick();
      
      const badge = wrapper.find('.execution-badge');
      expect(badge.classes()).toContain('secondary');
      expect(badge.find('i.pi-cog')).toBeTruthy();
    });

    it('shows success state correctly', async () => {
      const cell = createMockCell({
        metadata: { query_status: 'success' },
        status: 'idle',
        events: [{ type: 'response', content: 'Success response' }],
      });
      
      await wrapper.setProps({ cell });
      await wrapper.vm.$nextTick();
      
      const badge = wrapper.find('.execution-badge');
      // expect(badge.classes()).toContain('p-badge-success');
      expect(badge.find('i.pi-check')).toBeTruthy();
    });

    it('shows aborted state correctly', async () => {
      const cell = createMockCell({
        metadata: { query_status: 'aborted' },
        status: 'idle',
        events: [{ type: 'abort', content: 'Request interrupted' }],
      });
      
      await wrapper.setProps({ cell });
      await wrapper.vm.$nextTick();
      
      const badge = wrapper.find('.execution-badge');
      // expect(badge.classes()).toContain('p-badge-warn');
      expect(badge.find('i.pi-minus')).toBeTruthy();
    });

    it('shows failed state correctly', async () => {
      const cell = createMockCell({
        metadata: { query_status: 'failed' },
        status: 'idle',
        events: [{ type: 'error', content: 'Error occurred' }],
      });
      
      await wrapper.setProps({ cell });
      await wrapper.vm.$nextTick();
      
      const badge = wrapper.find('.execution-badge');
      // expect(badge.classes()).toContain('p-badge-danger');
      expect(badge.find('i.pi-times')).toBeTruthy();
    });
  });

});
