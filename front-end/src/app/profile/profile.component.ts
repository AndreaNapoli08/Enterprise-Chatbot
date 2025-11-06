import { Component, Input } from '@angular/core';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-profile',
  imports: [],
  templateUrl: './profile.component.html',
  styleUrl: './profile.component.css'
})
export class Profile {
  @Input() initials: string = '';
  @Input() name: string | null = null;
  @Input() surname: string | null = null;
  @Input() email: string | null = null
  @Input() role: string | null = null;

  constructor(private authService: AuthService) {}
  logout() {
    this.authService.logout();
  }
}
