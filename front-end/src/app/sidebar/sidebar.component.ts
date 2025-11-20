import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, ElementRef, EventEmitter, HostListener, Input, Output, ViewChild } from '@angular/core';
import { AuthService } from '../services/auth.service';
import { take } from 'rxjs';
import { FormsModule } from '@angular/forms';
import { ChatSession } from '../interfaces/chat_session';
import { Router } from '@angular/router';
import { Profile } from '../profile/profile.component';

@Component({
  selector: 'sidebar',
  imports: [CommonModule, FormsModule, Profile],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.css']
})
export class Sidebar {
  @Input() sessions: any;
  @ViewChild('drawer') drawer!: ElementRef;
  @ViewChild('renameInputField') renameInputField!: ElementRef<HTMLInputElement>;
  @Output() loadHistory = new EventEmitter<string>();
  @Input() currentSession!: string;
  @Output() sidebarState = new EventEmitter<boolean>();

  // variabili per informazioni utente
  @Input() initials: string = '';
  @Input() name: string | null = null;
  @Input() surname: string | null = null;
  @Input() email: string | null = null
  @Input() role: string | null = null;

  constructor( 
    private router: Router
  ) {}

  // menu rinomina o cancella chat
  openMenu: number | null = null;
  dropdownTop = 0;
  dropdownLeft = 0;
  showRenameModal: boolean = false;
  currentSessionToRename: string = "";
  renameInput: string = "";

  showDeleteModal: boolean = false;
  currentSessionToDelete: string = "";

  // Variabili per il modale di ricerca chat
  showSearchModal: boolean = false;
  searchQuery: string = '';
  filteredSessions: ChatSession[] = [];

  isChatExpanded: boolean = true;

  //sidebar ridimensionabile
  isResizing = false;
  startX = 0;
  startWidth = 0;

  openDrawer() {
    const el = this.drawer.nativeElement;
    el.classList.remove('-translate-x-full');
    this.sidebarState.emit(true); 
  }

  closeDrawer() {
    const el = this.drawer.nativeElement;
    el.classList.add('-translate-x-full');
    this.sidebarState.emit(false);
  }

  openDropdown(event: MouseEvent, trigger: HTMLElement, index: number) {
    event.stopPropagation();

    const rect = trigger.getBoundingClientRect();
    const dropdownHeight = 80; // altezza stimata del menu dropdown
    const margin = 4; // margine tra bottone e dropdown
    const windowHeight = window.innerHeight;

    // Calcola se c'è spazio sotto
    if (rect.bottom + dropdownHeight + margin > windowHeight) {
      // Non c'è abbastanza spazio sotto: apri sopra
      this.dropdownTop = rect.top - dropdownHeight - margin - 10;
    } else {
      // C'è spazio: apri sotto
      this.dropdownTop = rect.bottom + margin;
    }

    // Allinea a destra del bottone
    this.dropdownLeft = rect.right - 160;
    this.openMenu = this.openMenu === index ? null : index;
  }

  @HostListener('document:click')
  close() {
    this.openMenu = null;
  }

  // Metodo per aprire il modale
  openRenameModal(sessionId: string, sessionTitle: string) {
    this.currentSessionToRename = sessionId;
    this.showRenameModal = true;
    this.renameInput = sessionTitle && sessionTitle.trim() !== "" 
    ? sessionTitle 
    : sessionId;
    setTimeout(() => {
      this.renameInputField.nativeElement.focus();
      this.renameInputField.nativeElement.select(); 
    }, 0);
  }

  closeRenameModal() {
    this.showRenameModal = false;
    this.currentSessionToRename = "";
  }

  renameSession() {
    if (!this.currentSessionToRename) return;

    const sessionId = this.currentSessionToRename;
    const newTitle = this.renameInput.trim();

    fetch(`http://localhost:5050/chat/update_session_title/${sessionId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_title: newTitle })
    })
    .then(res => {
      if (!res.ok) throw new Error("Errore durante l’update");
      return res.json();
    })
    .then(data => {
      console.log("Titolo aggiornato nel DB:", data);

      // Aggiorna la UI locale
      const session = this.sessions.find((s: ChatSession) => s.id === sessionId);
      if (session) {
        session.title = newTitle;
      }

      // Chiudi modale
      this.closeRenameModal();
    })
    .catch(err => {
      console.error("Errore update title:", err);
    });
  }

  openDeleteModal(sessionId: string) {
    this.showDeleteModal = true;
    this.currentSessionToDelete = sessionId;
  }

  closeDeleteModal() {
    this.showDeleteModal = false;
    this.currentSessionToDelete = "";
  }

  deleteSession(sessionId: string) {
    fetch(`http://localhost:5050/chat/delete_session/${sessionId}`, {
      method: 'DELETE'
    })
    .then(res => {
      if (!res.ok) throw new Error("Errore nell'eliminazione");
      return res.json();
    })
    .then(() => {
      // Aggiorno localmente l'elenco delle sessioni
      this.sessions = this.sessions.filter((s: ChatSession) => s.id !== sessionId);
      this.router.navigateByUrl('/', { skipLocationChange: true }).then(() => {
        this.router.navigate(['/home']);
      });
    })
    .catch(err => console.error(err));
  }

  createNewChat() {
    this.currentSession = "";
    this.router.navigateByUrl('/', { skipLocationChange: true }).then(() => {
      this.router.navigate(['/home']);
    });
  }

  loadSession(sessionId: string) {
    this.currentSession = sessionId;
    this.loadHistory.emit(sessionId);
  }

  // Apri il modale di ricerca
  searchChat() {
    this.showSearchModal = true;
    this.searchQuery = '';
    this.filteredSessions = [...this.sessions]; // inizialmente tutti
  }

  // Chiudi modale
  closeSearchModal() {
    this.showSearchModal = false;
    this.searchQuery = '';
    this.filteredSessions = [];
  }

  // Filtra le sessioni in base al testo della ricerca
  filterSessions() {
    const query = this.searchQuery.toLowerCase().trim();
    this.filteredSessions = this.sessions.filter((s: ChatSession) => {
      const title = s.title ? s.title.toLowerCase() : '';
      const id = s.id.toLowerCase();
      return title.includes(query) || id.includes(query);
    });
  }

  // Carica la sessione selezionata dal risultato
  selectSession(sessionId: string) {
    this.loadSession(sessionId);
    this.closeSearchModal();
  }

  toggleChat() {
    this.isChatExpanded = !this.isChatExpanded;
  }

  startResize(event: MouseEvent) {
    this.isResizing = true;
    this.startX = event.clientX;
    this.startWidth = this.drawer.nativeElement.offsetWidth;

    document.addEventListener("mousemove", this.resizeDrawer);
    document.addEventListener("mouseup", this.stopResize);
  }

  resizeDrawer = (event: MouseEvent) => {
    if (!this.isResizing) return;
    const newWidth = this.startWidth + (event.clientX - this.startX);
    // Limiti min/max della sidebar
    const width = Math.min(Math.max(newWidth, 180), 500);
    this.drawer.nativeElement.style.width = width + "px";
  }

  stopResize = () => {
    this.isResizing = false;
    document.removeEventListener("mousemove", this.resizeDrawer);
    document.removeEventListener("mouseup", this.stopResize);
  };
}

