import { ApplicationConfig, provideZoneChangeDetection, importProvidersFrom } from '@angular/core';
import { provideHttpClient, withFetch } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import {
  LucideAngularModule,
  Activity,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Brain,
  CheckCircle,
  Download,
  FileText,
  Gauge,
  HeartPulse,
  Info,
  LayoutDashboard,
  Play,
  Plus,
  Server,
  Shield,
  Sparkles,
  Workflow,
  X
} from 'lucide-angular';

import { routes } from './app.routes';

/**
 * Standalone application configuration (Angular 18, no NgModules).
 * Lucide icons are registered once here and injected where needed.
 */
export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(withFetch()),
    importProvidersFrom(
      LucideAngularModule.pick({
        Activity, AlertTriangle, ArrowRight, BarChart3, Brain, CheckCircle,
        Download, FileText, Gauge, HeartPulse, Info, LayoutDashboard, Play,
        Plus, Server, Shield, Sparkles, Workflow, X
      })
    )
  ]
};
