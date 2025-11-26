import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { ChatBubble } from './chat-bubble.component';
import { FormsModule } from '@angular/forms';
import { ChatService } from '../services/chat.service';
import { AuthService } from '../services/auth.service';
import { MessageBusService } from '../services/message-bus.service';
import { of } from 'rxjs';

describe('ChatBubble Component', () => {
  let component: ChatBubble;
  let fixture: ComponentFixture<ChatBubble>;
  let chatServiceMock: any;
  let authServiceMock: any;
  let messageBusMock: any;

  beforeEach(async () => {
    chatServiceMock = {
      sendMessage: jasmine.createSpy('sendMessage').and.returnValue(of([{ text: 'Bot reply' }]))
    };

    authServiceMock = {
      getCurrentUser: jasmine.createSpy('getCurrentUser').and.returnValue(of({ email: 'test@example.com' }))
    };

    messageBusMock = { sendMessage: jasmine.createSpy('sendMessage') };

    await TestBed.configureTestingModule({
      imports: [ChatBubble, FormsModule],
      providers: [
        { provide: ChatService, useValue: chatServiceMock },
        { provide: AuthService, useValue: authServiceMock },
        { provide: MessageBusService, useValue: messageBusMock }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ChatBubble);
    component = fixture.componentInstance;
    component.message = { text: 'Hello', role: 'user', time: '12:00' };
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should emit botResponse and change states for sendButtonPayload', fakeAsync(() => {
    spyOn(component.botResponse, 'emit');
    spyOn(component.stateChangeLoading, 'emit');
    spyOn(component.stateChangeWaitingAnswer, 'emit');
    spyOn(component.stateChangeConversation, 'emit');

    component.sendButtonPayload('/choose_document');
    tick();
    expect(component.botResponse.emit).toHaveBeenCalled();
    expect(component.stateChangeLoading.emit).toHaveBeenCalledWith(true);

    component.sendButtonPayload('/choose_yes');
    tick();
    expect(component.stateChangeLoading.emit).toHaveBeenCalledWith(true);
    expect(component.stateChangeWaitingAnswer.emit).toHaveBeenCalledWith(false);

    component.sendButtonPayload('/yes_close_conversation');
    tick();
    expect(component.stateChangeConversation.emit).toHaveBeenCalledWith(true);
  }));

  it('should increment and decrement peopleCount', () => {
    const initial = component.peopleCount;
    component.incrementPeople();
    expect(component.peopleCount).toBe(initial + 1);
    component.decrementPeople();
    expect(component.peopleCount).toBe(initial);
  });

  it('should send selected features', fakeAsync(() => {
    spyOn(component.stateChangeLoading, 'emit');
    spyOn(component.botResponse, 'emit');

    component.featuresList[0].selected = true;
    component.featuresList[2].selected = true;

    component.sendSelectedFeatures();
    tick();

    expect(component.botResponse.emit).toHaveBeenCalled();
    expect(component.stateChangeLoading.emit).toHaveBeenCalledWith(true);
  }));

  it('should send people count', fakeAsync(() => {
    spyOn(component.botResponse, 'emit');
    component.sendPeopleCount();
    tick();
    expect(component.botResponse.emit).toHaveBeenCalled();
    expect(component.disabledInputs).toBeTrue();
  }));

  it('should send new password', fakeAsync(() => {
    spyOn(component.botResponse, 'emit');
    spyOn(component.stateChangeLoading, 'emit');

    component.passwords['oldPassword'] = 'oldPass';
    component.passwords['newPassword'] = 'newPass';

    component.sendNewPassword();
    tick();

    expect(component.botResponse.emit).toHaveBeenCalled();
    expect(component.stateChangeLoading.emit).toHaveBeenCalledWith(true);
    expect(component.disabledInputs).toBeTrue();
  }));

  it('should toggle password visibility', () => {
    expect(component.passwordVisibility['old']).toBeFalse();
    component.togglePasswordVisibility('old');
    expect(component.passwordVisibility['old']).toBeTrue();
  });

  it('should check long button layout', () => {
    const buttons = [{ title: 'Short' }, { title: 'This is a long button' }];
    expect(component.isLongButtonLayout(buttons)).toBeTrue();
  });

  it('should download a file', () => {
    spyOn(document.body, 'appendChild').and.callThrough();
    spyOn(document.body, 'removeChild').and.callThrough();

    const fileUrl = 'https://example.com/file.pdf';
    const fileName = 'file.pdf';

    component.downloadFile(fileUrl, fileName);

    expect(document.body.appendChild).toHaveBeenCalled();
    expect(document.body.removeChild).toHaveBeenCalled();
  });

  it('should send date', fakeAsync(() => {
    spyOn(component.botResponse, 'emit');

    component.selectedDate = new Date(2025, 10, 25); // 25 Nov 2025
    component.startTime = '14:00';
    component.duration = 1;

    component.sendDate();
    tick();

    expect(component.botResponse.emit).toHaveBeenCalled();
    expect(component.disabledInputs).toBeTrue();
  }));
});
