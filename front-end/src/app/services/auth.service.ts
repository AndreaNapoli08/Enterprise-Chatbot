import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { User } from '../interfaces/user';
import { Observable, map, catchError, of } from 'rxjs';

@Injectable({
  providedIn: 'root',
})

export class AuthService {
  private apiUrl = 'http://localhost:5050/users';
  private loggedIn: boolean = false;

  constructor(private router: Router, private http: HttpClient) {}
  
  login(email: string, password: string): Observable<boolean> {
    return this.http.post<User>(`${this.apiUrl}/login`, { email, password }).pipe(
      map((user) => {
        if (user && user.email) {
          this.loggedIn = true;
          localStorage.setItem('loggedIn', 'true');
          localStorage.setItem('email', user.email);
          return true;
        }
        return false;
      }),
      catchError((err) => {
        console.error('Errore login:', err);
        return of(false);
      })
    );
  }

  isLoggedIn() {
    return this.loggedIn = localStorage.getItem('loggedIn') === 'true';
  }

  getCurrentUser(): Observable<User | null> {
    const email = localStorage.getItem('email');
    if (!email) {
      return of(null);
    }

    return this.http.get<User>(`${this.apiUrl}/${email}`).pipe(
      map(user => user || null),
      catchError(err => {
        console.error('Errore nel recupero utente:', err);
        return of(null);
      })
    );
  }
  
  logout() {
    this.loggedIn = false;
    localStorage.removeItem('loggedIn');
    localStorage.removeItem('email');
    this.router.navigate(['/login']);
  }
}