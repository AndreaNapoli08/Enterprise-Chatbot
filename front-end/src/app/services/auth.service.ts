import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { User } from '../interfaces/user';
import { Observable, map } from 'rxjs';

@Injectable({
  providedIn: 'root',
})

export class AuthService {
  private apiUrl = 'http://localhost:3000/users';
  private loggedIn: boolean = false;

  constructor(private router: Router, private http: HttpClient) {}
  
  login(email: string, password: string): Observable<boolean> {
    return this.http.get<User[]>(this.apiUrl).pipe(
      map((users) => {
        const user = users.find(u => u.email === email && u.password === password);
        this.loggedIn = !!user;
        if (this.loggedIn) {
          localStorage.setItem('loggedIn', 'true');
          localStorage.setItem('email', email);
        }
        return this.loggedIn;
      })
    );
  }

  isLoggedIn() {
    this.loggedIn = localStorage.getItem('loggedIn') === 'true';
    return this.loggedIn;
  }

  getCurrentUser(): Observable<User | string> {
    const email = localStorage.getItem('email');
    if (!email) return new Observable(obs => obs.next(""));

    return this.http.get<User[]>(this.apiUrl).pipe(
      map(users => users.find(u => u.email === email) || "")
    );
  }
  
  logout() {
    this.loggedIn = false;
    localStorage.removeItem('loggedIn');
    localStorage.removeItem('email');
    this.router.navigate(['/login']);
  }
}