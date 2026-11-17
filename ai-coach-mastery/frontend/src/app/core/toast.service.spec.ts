import { fakeAsync, tick } from '@angular/core/testing';

import { ToastService } from './toast.service';

/** ToastService — happy path, negative path and edge cases. */
describe('ToastService', () => {
  let service: ToastService;

  beforeEach(() => {
    service = new ToastService();
  });

  // --- Happy path -----------------------------------------------------------

  it('queues a success toast and auto-dismisses after TTL', fakeAsync(() => {
    service.success('Saved');
    expect(service.toasts().length).toBe(1);
    expect(service.toasts()[0].kind).toBe('success');

    tick(3500);
    expect(service.toasts().length).toBe(0);
  }));

  // --- Negative path ----------------------------------------------------------

  it('error toasts use a longer TTL', fakeAsync(() => {
    service.error('Boom');
    tick(3500);
    expect(service.toasts().length).toBe(1); // still visible at 3.5s

    tick(1500);
    expect(service.toasts().length).toBe(0); // gone after 5s
  }));

  // --- Edge cases ----------------------------------------------------------------

  it('edge: multiple toasts keep unique ids and order', fakeAsync(() => {
    service.info('one');
    service.info('two');
    service.info('three');
    const ids = service.toasts().map((t) => t.id);
    expect(new Set(ids).size).toBe(3);
    expect(service.toasts().map((t) => t.message)).toEqual(['one', 'two', 'three']);
    tick(3500);
  }));

  it('edge: manual dismiss removes only the targeted toast', fakeAsync(() => {
    service.info('a');
    service.info('b');
    const first = service.toasts()[0].id;
    service.dismiss(first);
    expect(service.toasts().length).toBe(1);
    expect(service.toasts()[0].message).toBe('b');
    tick(3500);
  }));

  it('edge: dismissing an unknown id is a no-op', fakeAsync(() => {
    service.info('solo');
    service.dismiss(9999);
    expect(service.toasts().length).toBe(1);
    tick(3500);
  }));
});
