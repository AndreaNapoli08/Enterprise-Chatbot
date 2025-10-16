import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { AuthService } from '../services/auth.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-login',
  imports: [FormsModule, CommonModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class Login {
  email = '';
  password = '';
  loginFailed: boolean = false;
  passwordVisible = false;

  constructor(private authService: AuthService, private router: Router) {}

  onSubmit() {
    if (this.email === '' || this.password === '') {
      alert('Compilare tutti i campi');
    } else {
      const success = this.authService.login(this.email, this.password);
      if (success) {
        this.router.navigate(['/home']); // Reindirizza alla pagina home se il login ha avuto successo
      } else {
        alert('Utente non trovato');
        this.loginFailed = true;
      }
    }
  }

  togglePasswordVisibility(): void {
    this.passwordVisible = !this.passwordVisible;
  }
}

