import { Routes } from '@angular/router';

/** Lazy standalone routes. */
export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./dashboard/dashboard.component').then((m) => m.DashboardComponent)
  },
  {
    path: 'engagements/:id',
    loadComponent: () =>
      import('./lifecycle/lifecycle.component').then((m) => m.LifecycleComponent)
  },
  { path: '**', redirectTo: '' }
];
