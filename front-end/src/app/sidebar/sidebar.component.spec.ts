import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';

import { Sidebar } from './sidebar.component';
import { Router } from '@angular/router';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { AuthService } from '../services/auth.service';
import { of } from 'rxjs';

describe('SidebarComponent', () => {
  let component: Sidebar;
  let fixture: ComponentFixture<Sidebar>;
  let routerSpy: any;

  const sampleSessions = [
    { id: 's1', title: 'First session' },
    { id: 's2', title: '' },
    { id: 'abc', title: 'Chat Three' }
  ];

  beforeEach(async () => {
    routerSpy = jasmine.createSpyObj('Router', ['navigateByUrl', 'navigate']);
    routerSpy.navigateByUrl.and.returnValue(Promise.resolve(true));

    const authStub: Partial<AuthService> = {
      login: (_e: string, _p: string) => of(true),
      isLoggedIn: () => false,
      getCurrentUser: () => of(null),
      logout: () => {}
    };

    await TestBed.configureTestingModule({
      imports: [Sidebar],
      providers: [
        { provide: Router, useValue: routerSpy },
        provideHttpClientTesting(),
        { provide: AuthService, useValue: authStub }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(Sidebar);
    component = fixture.componentInstance;

    // run initial change detection
    fixture.detectChanges();

    // mock element refs used by the component AFTER change detection
    component.drawer = {
      nativeElement: {
        classList: { add: jasmine.createSpy('add'), remove: jasmine.createSpy('remove') },
        offsetWidth: 200,
        style: { width: '' }
      }
    } as any;

    component.renameInputField = { nativeElement: { focus: jasmine.createSpy('focus'), select: jasmine.createSpy('select') } } as any;
    component.searchInputField = { nativeElement: { focus: jasmine.createSpy('focus') } } as any;

    component.sessions = JSON.parse(JSON.stringify(sampleSessions));
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('openDrawer should remove translate class and emit true', () => {
    spyOn(component.sidebarState, 'emit');
    component.openDrawer();
    expect(component.drawer.nativeElement.classList.remove).toHaveBeenCalledWith('-translate-x-full');
    expect(component.sidebarState.emit).toHaveBeenCalledWith(true);
  });

  it('closeDrawer should add translate class and emit false', () => {
    spyOn(component.sidebarState, 'emit');
    component.closeDrawer();
    expect(component.drawer.nativeElement.classList.add).toHaveBeenCalledWith('-translate-x-full');
    expect(component.sidebarState.emit).toHaveBeenCalledWith(false);
  });

  it('openDropdown calculates positions and toggles openMenu', () => {
    const fakeRect = { top: 100, bottom: 150, right: 300 } as DOMRect;
    const trigger = { getBoundingClientRect: () => fakeRect } as any;
    const event = { stopPropagation: jasmine.createSpy('stop') } as any;

    // ensure window height large so opens below
    (window as any).innerHeight = 1000;
    component.openDropdown(event as any, trigger, 1);
    expect(event.stopPropagation).toHaveBeenCalled();
    expect(component.dropdownTop).toBe(fakeRect.bottom + 4);
    expect(component.dropdownLeft).toBe(fakeRect.right - 160);
    expect(component.openMenu).toBe(1);

    // calling again toggles off
    component.openDropdown(event as any, trigger, 1);
    expect(component.openMenu).toBeNull();
  });

  it('close should set openMenu to null', () => {
    component.openMenu = 2;
    component.close();
    expect(component.openMenu).toBeNull();
  });

  it('openRenameModal sets fields (with title)', fakeAsync(() => {
    component.openRenameModal('s1', 'Title');
    tick(0);
    expect(component.currentSessionToRename).toBe('s1');
    expect(component.showRenameModal).toBeTrue();
    expect(component.renameInput).toBe('Title');
  }));

  it('openRenameModal uses id when title empty', fakeAsync(() => {
    component.openRenameModal('s2', '');
    tick(0);
    expect(component.renameInput).toBe('s2');
  }));

  it('renameSession should call fetch and update local title', async () => {
    component.sessions = [{ id: 's1', title: 'Old' } as any];
    component.currentSessionToRename = 's1';
    component.renameInput = 'New Title';

    spyOn(window as any, 'fetch').and.returnValue(Promise.resolve({ ok: true, json: () => Promise.resolve({}) }));

    component.renameSession();

    // wait microtasks for promises
    await Promise.resolve();
    await Promise.resolve();

    expect((component.sessions as any[])[0].title).toBe('New Title');
    expect(component.showRenameModal).toBeFalse();
  });

  it('openDeleteModal and closeDeleteModal manage state', () => {
    component.openDeleteModal('s1');
    expect(component.showDeleteModal).toBeTrue();
    expect(component.currentSessionToDelete).toBe('s1');

    component.closeDeleteModal();
    expect(component.showDeleteModal).toBeFalse();
    expect(component.currentSessionToDelete).toBe('');
  });

  it('deleteSession calls fetch, updates sessions and navigates when current session deleted', async () => {
    component.sessions = [{ id: 's1', title: 'A' }, { id: 's2', title: 'B' }] as any;
    component.currentSession = 's1';

    spyOn(window as any, 'fetch').and.returnValue(Promise.resolve({ ok: true, json: () => Promise.resolve({}) }));

    component.deleteSession('s1');

    await Promise.resolve();
    await Promise.resolve();

    expect((component.sessions as any[]).find(s => s.id === 's1')).toBeUndefined();
    expect(routerSpy.navigateByUrl).toHaveBeenCalled();
    expect(component.showDeleteModal).toBeFalse();
  });

  it('createNewChat navigates to home', () => {
    component.createNewChat();
    expect(routerSpy.navigateByUrl).toHaveBeenCalled();
  });

  it('loadSession sets currentSession and emits event', () => {
    spyOn(component.loadHistory, 'emit');
    component.loadSession('abc');
    expect(component.currentSession).toBe('abc');
    expect(component.loadHistory.emit).toHaveBeenCalledWith('abc');
  });

  it('searchChat opens search modal', fakeAsync(() => {
    component.searchChat();
    tick(0);
    expect(component.showSearchModal).toBeTrue();
    expect(component.searchQuery).toBe('');
    expect(component.filteredSessions.length).toBe(component.sessions.length);
  }));

  it('closeSearchModal resets search state', () => {
    component.showSearchModal = true;
    component.searchQuery = 'x';
    component.filteredSessions = [{ id: 'x' } as any];
    component.closeSearchModal();
    expect(component.showSearchModal).toBeFalse();
    expect(component.searchQuery).toBe('');
    expect(component.filteredSessions.length).toBe(0);
  });

  it('filterSessions filters by title or id', () => {
    component.sessions = JSON.parse(JSON.stringify(sampleSessions));
    component.searchQuery = 'chat';
    component.filterSessions();
    expect(component.filteredSessions.length).toBe(1);
    expect(component.filteredSessions[0].id).toBe('abc');

    component.searchQuery = 's1';
    component.filterSessions();
    expect(component.filteredSessions.length).toBe(1);
    expect(component.filteredSessions[0].id).toBe('s1');
  });

  it('selectSession loads and closes search modal', () => {
    spyOn(component.loadHistory, 'emit');
    component.showSearchModal = true;
    component.selectSession('s1');
    expect(component.loadHistory.emit).toHaveBeenCalledWith('s1');
    expect(component.showSearchModal).toBeFalse();
  });

  it('toggleChat toggles isChatExpanded', () => {
    const before = component.isChatExpanded;
    component.toggleChat();
    expect(component.isChatExpanded).toBe(!before);
  });

  it('startResize, resizeDrawer and stopResize adjust width', () => {
    // start resize
    const evt = { clientX: 100 } as any;
    component.startResize(evt as MouseEvent);
    expect(component.isResizing).toBeTrue();

    // simulate moving mouse to expand by +50
    component.resizeDrawer({ clientX: 150 } as MouseEvent);
    const expected = component.startWidth + (150 - 100);
    expect(component.drawer.nativeElement.style.width).toBe(expected + 'px');

    // stop
    component.stopResize();
    expect(component.isResizing).toBeFalse();
  });
});
