import { Routes } from '@angular/router';
import { Home } from './home/home.component';
//import { AuthGuard } from './auth.guard'; 

export const routes: Routes = [
  //{ path: 'login', component: LoginComponent },
  { path: 'home', component: Home},
  //{ path: '', redirectTo: '/login', pathMatch: 'full' },
];