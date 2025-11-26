import { Component, ElementRef, HostListener, Input, ViewChild } from '@angular/core';
import { AuthService } from '../services/auth.service';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-profile',
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.css'],
  standalone: true,
  imports: [CommonModule, FormsModule]
})
export class Profile {
  @Input() initials: string = '';
  @Input() name: string | null = null;
  @Input() surname: string | null = null;
  @Input() email: string | null = null;
  @Input() role: string | null = null;
  @Input() expanded: boolean = false;

  isOpen = false;

  constructor(private authService: AuthService, private host: ElementRef) {}

  toggleDropdown(event?: MouseEvent) {
    if (event) event.stopPropagation();
    this.isOpen = !this.isOpen;
  }

  closeDropdown() {
    this.isOpen = false;
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent) {
    // Se il click è fuori dal componente, chiudi il dropdown
    const target = event.target as Node;
    if (!this.host?.nativeElement.contains(target)) {
      this.closeDropdown();
    }
  }

  logout() {
    // assicurati di chiudere il dropdown quando fai logout
    this.closeDropdown();
    this.authService.logout();
  }
}