import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Profile } from './profile.component';
import { AuthService } from '../services/auth.service';
import { ElementRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

describe('Profile Component', () => {
  let component: Profile;
  let fixture: ComponentFixture<Profile>;
  let authServiceMock: any;
  let hostElement: HTMLElement;

  beforeEach(async () => {
    authServiceMock = {
      logout: jasmine.createSpy('logout')
    };

    // Simuliamo il nativeElement del componente
    hostElement = document.createElement('div');

    await TestBed.configureTestingModule({
      imports: [Profile, FormsModule, CommonModule],
      providers: [
        { provide: AuthService, useValue: authServiceMock },
        { provide: ElementRef, useValue: new ElementRef(hostElement) }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(Profile);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should toggle dropdown state', () => {
    expect(component.isOpen).toBeFalse();
    component.toggleDropdown();
    expect(component.isOpen).toBeTrue();
    component.toggleDropdown();
    expect(component.isOpen).toBeFalse();
  });

  it('should stop propagation when toggling dropdown with event', () => {
    const event = { stopPropagation: jasmine.createSpy('stopPropagation') } as any;
    component.toggleDropdown(event);
    expect(event.stopPropagation).toHaveBeenCalled();
  });

  it('should close dropdown manually', () => {
    component.isOpen = true;
    component.closeDropdown();
    expect(component.isOpen).toBeFalse();
  });

  it('should close dropdown on document click outside', () => {
    component.isOpen = true;
    const outsideEvent = { target: document.createElement('div') } as unknown as MouseEvent;
    component.onDocumentClick(outsideEvent);
    expect(component.isOpen).toBeFalse();
  });

  it('should not close dropdown on document click inside', () => {
    component.isOpen = true;

    // Prendiamo il nativeElement reale del fixture
    const insideElement = fixture.nativeElement.querySelector('div');
    
    // Simuliamo un click sull'elemento interno
    const insideEvent = new MouseEvent('click', { bubbles: true });
    Object.defineProperty(insideEvent, 'target', { value: insideElement });

    component.onDocumentClick(insideEvent);

    expect(component.isOpen).toBeTrue();
  });

  it('should logout and close dropdown', () => {
    component.isOpen = true;
    component.logout();
    expect(authServiceMock.logout).toHaveBeenCalled();
    expect(component.isOpen).toBeFalse();
  });

  it('should set @Input properties correctly', () => {
    component.initials = 'AB';
    component.name = 'Alice';
    component.surname = 'Bianchi';
    component.email = 'alice@example.com';
    component.role = 'manager';
    component.expanded = true;

    expect(component.initials).toBe('AB');
    expect(component.name).toBe('Alice');
    expect(component.surname).toBe('Bianchi');
    expect(component.email).toBe('alice@example.com');
    expect(component.role).toBe('manager');
    expect(component.expanded).toBeTrue();
  });
});