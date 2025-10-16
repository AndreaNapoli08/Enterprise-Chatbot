import { Routes } from '@angular/router';
import { Home } from './home/home.component';
//import { AuthGuard } from './auth.guard'; 
import { Login } from './login/login.component';

export const routes: Routes = [
  //{ path: 'login', component: LoginComponent },
  { path: 'home', component: Home},
  { path: 'login', component: Login },
  //{ path: '', redirectTo: '/login', pathMatch: 'full' },
];