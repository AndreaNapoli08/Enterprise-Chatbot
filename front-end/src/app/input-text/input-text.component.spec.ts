import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { InputText } from './input-text.component';
import { FormsModule } from '@angular/forms';
import { ChatService } from '../services/chat.service';
import { AuthService } from '../services/auth.service';
import { Router } from '@angular/router';
import { of } from 'rxjs';
import { Message } from '../interfaces/message';

describe('InputText Component', () => {
  let component: InputText;
  let fixture: ComponentFixture<InputText>;
  let chatServiceMock: any;
  let authServiceMock: any;
  let routerMock: any;

  beforeEach(async () => {
    // Mock dei servizi
    chatServiceMock = {
      sendMessage: jasmine.createSpy('sendMessage').and.returnValue(of([{ text: 'Bot response' }]))
    };

    authServiceMock = {
      getCurrentUser: jasmine.createSpy('getCurrentUser').and.returnValue(of({ email: 'test@example.com' }))
    };

    routerMock = {
      navigateByUrl: jasmine.createSpy('navigateByUrl').and.returnValue(Promise.resolve(true)),
      navigate: jasmine.createSpy('navigate').and.returnValue(Promise.resolve(true))
    };

    await TestBed.configureTestingModule({
      imports: [
        InputText,  // componente standalone
        FormsModule
      ],
      providers: [
        { provide: ChatService, useValue: chatServiceMock },
        { provide: AuthService, useValue: authServiceMock },
        { provide: Router, useValue: routerMock }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(InputText);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should emit stateEmptyInput when input changes', () => {
    spyOn(component.stateEmptyInput, 'emit');

    component.onTextChange('test');
    expect(component.stateEmptyInput.emit).toHaveBeenCalledWith(false);

    component.onTextChange('   ');
    expect(component.stateEmptyInput.emit).toHaveBeenCalledWith(true);
  });

  it('should not submit empty message', () => {
    spyOn(component.submitAnswer, 'emit');
    component.answer = '   ';
    component.onSubmit();
    expect(component.submitAnswer.emit).not.toHaveBeenCalled();
  });

  it('should submit user message and bot response', fakeAsync(() => {
    spyOn(component.submitAnswer, 'emit');

    component.answer = 'Hello';
    component.onSubmit();
    tick();

    // Messaggio utente
    expect(component.submitAnswer.emit).toHaveBeenCalledWith(
      jasmine.objectContaining({
        text: 'Hello',
        role: 'user',
        time: jasmine.any(String)
      })
    );

    // Messaggio bot
    expect(component.submitAnswer.emit).toHaveBeenCalledWith(
      jasmine.objectContaining({
        text: 'Bot response',
        role: 'bot',
        time: jasmine.any(String)
      })
    );

    // L'input viene resettato
    expect(component.answer).toBe('');
  }));

  it('should call getCurrentUser and sendMessage using mocks', fakeAsync(() => {
    component.answer = 'Hello';
    component.onSubmit();
    tick();

    expect(authServiceMock.getCurrentUser).toHaveBeenCalled();
    expect(chatServiceMock.sendMessage).toHaveBeenCalledWith('Hello', 'test@example.com');
  }));

  it('should disable input and end conversation when humanOperator changes to true', () => {
    component.disabled = false;
    component.conversationEnded = false;

    component.ngOnChanges({ 
      humanOperator: { currentValue: true, previousValue: false, firstChange: false, isFirstChange: () => false } 
    });

    expect(component.disabled).toBeTrue();
    expect(component.conversationEnded).toBeTrue();
  });

  it('should call router to create new chat', fakeAsync(() => {
    component.createNewChat();
    tick();
    expect(routerMock.navigateByUrl).toHaveBeenCalledWith('/', { skipLocationChange: true });
    expect(routerMock.navigate).toHaveBeenCalledWith(['/home']);
  }));
});
