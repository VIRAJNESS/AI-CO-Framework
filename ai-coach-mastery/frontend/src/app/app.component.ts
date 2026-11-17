import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';

import { ToastService } from './core/toast.service';

/**
 * Executive console shell: Deep Navy sidebar, slate workspace, toast overlay.
 * Fully standalone (no NgModules).
 */
@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, LucideAngularModule],
  template: `
    <div class="flex min-h-screen bg-slate-100">
      <!-- Deep Navy sidebar -->
      <aside class="flex w-60 shrink-0 flex-col bg-navy text-white">
        <div class="flex items-center gap-3 border-b border-slate-700/60 px-5 py-5">
          <lucide-icon name="brain" class="h-7 w-7 text-sky"></lucide-icon>
          <div>
            <p class="text-sm font-bold leading-tight">AI Coach Mastery</p>
            <p class="text-[11px] text-slate-400">Executive Console</p>
          </div>
        </div>
        <nav class="flex-1 space-y-1 px-3 py-4">
          <a routerLink="/" routerLinkActive="bg-sky/20 text-sky"
             [routerLinkActiveOptions]="{ exact: true }"
             class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm
                    font-medium text-slate-300 transition hover:bg-white/5">
            <lucide-icon name="layout-dashboard" class="h-4 w-4"></lucide-icon>
            Portfolio
          </a>
        </nav>
        <div class="border-t border-slate-700/60 px-5 py-4">
          <span class="rounded bg-emerald-600/20 px-2 py-1 text-[11px]
                       font-semibold text-emerald-400">local-first • mock LLM</span>
        </div>
      </aside>

      <!-- Workspace -->
      <main class="min-w-0 flex-1 overflow-x-hidden p-6 lg:p-8">
        <router-outlet></router-outlet>
      </main>
    </div>

    <!-- Toast overlay -->
    <div class="pointer-events-none fixed bottom-5 right-5 z-50 flex w-80 flex-col gap-2">
      @for (toast of toasts.toasts(); track toast.id) {
        <div class="pointer-events-auto flex items-start gap-2 rounded-lg px-4 py-3
                    text-sm text-white shadow-lg"
             [class]="toast.kind === 'success' ? 'bg-emerald-600'
                      : toast.kind === 'error' ? 'bg-rose-600' : 'bg-sky'">
          <lucide-icon [name]="toast.kind === 'success' ? 'check-circle'
                              : toast.kind === 'error' ? 'alert-triangle' : 'info'"
                       class="mt-0.5 h-4 w-4 shrink-0"></lucide-icon>
          <span class="flex-1">{{ toast.message }}</span>
          <button class="opacity-70 hover:opacity-100"
                  (click)="toasts.dismiss(toast.id)">✕</button>
        </div>
      }
    </div>
  `
})
export class AppComponent {
  protected readonly toasts = inject(ToastService);
}
