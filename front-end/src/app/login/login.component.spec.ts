import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { AuthService } from '../services/auth.service';
import { of } from 'rxjs';
import { Router } from '@angular/router';

import { Login } from './login.component';

describe('LoginComponent', () => {
  let component: Login;
  let fixture: ComponentFixture<Login>;
  let authStub: Partial<AuthService>;
  let routerSpy: { navigate: jasmine.Spy };
  let toastEl: HTMLElement | null = null;

  beforeEach(async () => {
    authStub = {
      login: (_e: string, _p: string) => of(true),
      isLoggedIn: () => false,
      getCurrentUser: () => of(null),
      logout: () => {}
    };

    routerSpy = { navigate: jasmine.createSpy('navigate') };

    await TestBed.configureTestingModule({
      imports: [Login],
      providers: [
        provideHttpClientTesting(),
        { provide: AuthService, useValue: authStub },
        { provide: Router, useValue: routerSpy }
      ]
    })
    .compileComponents();

    // create toast container expected by showToast
    toastEl = document.createElement('div');
    toastEl.id = 'toast';
    document.body.appendChild(toastEl);

    fixture = TestBed.createComponent(Login);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => {
    if (toastEl && toastEl.parentElement) {
      toastEl.parentElement.removeChild(toastEl);
    }
    toastEl = null;
    localStorage.clear();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should not call auth.login and show toast when email or password empty', () => {
    const auth = TestBed.inject(AuthService) as any;
    spyOn(auth, 'login').and.callThrough();

    component.email = '';
    component.password = '';

    component.onSubmit();

    expect(auth.login).not.toHaveBeenCalled();
    expect(component.isLoading).toBeFalsy();
    const toast = document.getElementById('toast');
    expect(toast?.innerHTML).toContain('Compilare tutti i campi');
  });

  it('should login successfully, set localStorage and navigate to /home', () => {
    const auth = TestBed.inject(AuthService) as any;
    spyOn(auth, 'login').and.returnValue(of(true));
    spyOn(localStorage, 'setItem');

    component.email = 'user@example.com';
    component.password = 'secret';

    component.onSubmit();

    expect(auth.login).toHaveBeenCalledWith('user@example.com', 'secret');
    expect(localStorage.setItem).toHaveBeenCalledWith('email', 'user@example.com');
    expect((TestBed.inject(Router) as any).navigate).toHaveBeenCalledWith(['/home']);
  });

  it('should handle login failure, show toast and set flags', fakeAsync(() => {
    const auth = TestBed.inject(AuthService) as any;
    spyOn(auth, 'login').and.returnValue(of(false));

    component.email = 'bad@example.com';
    component.password = 'bad';

    component.onSubmit();

    expect(auth.login).toHaveBeenCalled();
    expect(component.loginFailed).toBeTrue();
    expect(component.isLoading).toBeFalse();
    const toast = document.getElementById('toast');
    expect(toast?.innerHTML).toContain('Utente non trovato');

    // toast is removed after 2000ms
    tick(2000);
    const toastDanger = document.getElementById('toast-danger');
    expect(toastDanger).toBeNull();
  }));

  it('togglePasswordVisibility should toggle the flag', () => {
    const before = component.passwordVisible;
    component.togglePasswordVisibility();
    expect(component.passwordVisible).toBe(!before);
    component.togglePasswordVisibility();
    expect(component.passwordVisible).toBe(before);
  });
});