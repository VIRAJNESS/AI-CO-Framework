import { bootstrapApplication } from '@angular/platform-browser';
import { Chart, registerables } from 'chart.js';

import { AppComponent } from './app/app.component';
import { appConfig } from './app/app.config';

// Register Chart.js controllers/scales/plugins once for the whole app.
Chart.register(...registerables);

// Standalone bootstrap — no NgModules anywhere in this app.
bootstrapApplication(AppComponent, appConfig).catch((err) => console.error(err));
