import { Routes } from '@angular/router';
import { Home } from './home/home.component';
import { AuthGuard } from './auth.guard'; 
import { Login } from './login/login.component';

export const routes: Routes = [
  { path: 'login', component: Login },
  //{ path: 'home', component: Home, canActivate: [AuthGuard]},
  { path: 'home', component: Home/*, canActivate: [AuthGuard]*/ },
  { path: '', redirectTo: '/login', pathMatch: 'full' },
];