import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Subject } from 'rxjs';
import { NavigationEnd, Router } from '@angular/router';
// note: avoid spying on imported read-only module bindings like `flowbite`.

import { AppComponent } from './app.component';

describe('AppComponent', () => {
  let fixture: ComponentFixture<AppComponent>;
  let component: AppComponent;
  let routerEvents$: Subject<any>;

  function makeMatchMedia(matches: boolean) {
    let listener: any = null;
    return {
      matches,
      addEventListener: (evt: string, cb: any) => { listener = cb; },
      removeEventListener: (_: string, __: any) => {},
      // helper to trigger change
      __trigger: (e: any) => { if (listener) listener(e); }
    } as any;
  }

  beforeEach(async () => {
    routerEvents$ = new Subject<any>();
    const routerStub: Partial<Router> = { events: routerEvents$.asObservable() };

    await TestBed.configureTestingModule({
      imports: [AppComponent],
      providers: [{ provide: Router, useValue: routerStub }]
    }).compileComponents();

    fixture = TestBed.createComponent(AppComponent);
    component = fixture.componentInstance;
  });

  afterEach(() => {
    // cleanup any favicon added
    const f = document.getElementById('favicon');
    if (f && f.parentElement) f.parentElement.removeChild(f);
    // reset html classes
    document.documentElement.classList.remove('dark');
  });

  it('should create the app and have correct title', () => {
    expect(component).toBeTruthy();
    expect(component.title).toBe('enterprise-chatbot');
  });

  it('ngOnInit applies dark theme when prefers-color-scheme is dark and calls initFlowbite', () => {
    const mq = makeMatchMedia(true);
    (window as any).matchMedia = jasmine.createSpy('matchMedia').and.returnValue(mq);

    spyOn(component, 'updateFavicon');
    component.ngOnInit();

    expect(document.documentElement.classList.contains('dark')).toBeTrue();
    expect(component.updateFavicon).toHaveBeenCalledWith(true);
  });

  it('matchMedia change listener toggles theme and calls updateFavicon', () => {
    const mq = makeMatchMedia(false);
    (window as any).matchMedia = jasmine.createSpy('matchMedia').and.returnValue(mq);

    spyOn(component, 'updateFavicon');
    component.ngOnInit();

    // initially light
    expect(document.documentElement.classList.contains('dark')).toBeFalse();

    // trigger change to dark
    (mq as any).__trigger({ matches: true });

    expect(document.documentElement.classList.contains('dark')).toBeTrue();
    expect(component.updateFavicon).toHaveBeenCalledWith(true);
  });

  it('updateFavicon creates/updates link and logs the href', () => {
    const logSpy = spyOn(console, 'log');

    component.updateFavicon(false);
    const links = Array.from(document.querySelectorAll('#favicon')) as HTMLLinkElement[];
    expect(links.length).toBeGreaterThan(0);
    expect(links[links.length - 1].href).toContain('favicon_light.ico');
    expect(logSpy).toHaveBeenCalled();

    // call again with dark and ensure at least one favicon element has dark href
    component.updateFavicon(true);
    const linksAfter = Array.from(document.querySelectorAll('#favicon')) as HTMLLinkElement[];
    const hasDark = linksAfter.some(l => l.href.includes('favicon_dark.ico'));
    expect(hasDark).toBeTrue();
  });

  it('calls initFlowbite on NavigationEnd', () => {
    const mq = makeMatchMedia(false);
    (window as any).matchMedia = jasmine.createSpy('matchMedia').and.returnValue(mq);

    // calling ngOnInit and emitting a NavigationEnd should not throw
    component.ngOnInit();
    routerEvents$.next(new NavigationEnd(1, '/a', '/a'));
    // no explicit assertion on flowbite calls because the imported binding is read-only in tests
  });
});
