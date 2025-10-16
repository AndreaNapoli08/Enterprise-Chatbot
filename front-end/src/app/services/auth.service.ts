import { Injectable } from '@angular/core';
import { Router } from '@angular/router';

@Injectable({
  providedIn: 'root',
})

export class AuthService {
  private users: { email: string; password: string }[] = [
    { email: 'user', password: 'ciao' },
  ];

  constructor(private router: Router) {}
  private loggedIn: boolean = false;

  login(email: string, password: string) {
    const user = this.users.find(
      (user) => user.email === email && user.password === password
    );
    this.loggedIn = user !== undefined;
    localStorage.setItem('loggedIn', this.loggedIn.toString());
    return this.loggedIn;
  }

  isLoggedIn() {
    this.loggedIn = localStorage.getItem('loggedIn') === 'true';
    return this.loggedIn;
  }

  logout() {
    this.loggedIn = false; 
    localStorage.setItem('loggedIn', this.loggedIn.toString());
    this.router.navigate(['/login']);
  }
}