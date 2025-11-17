import { CommonModule } from '@angular/common';
import { Component, ElementRef, HostListener, ViewChild } from '@angular/core';

@Component({
  selector: 'sidebar',
  imports: [CommonModule],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.css'
})
export class Sidebar {
  @ViewChild('drawer') drawer!: ElementRef;

  // menu rinomina o cancella chat
  openMenu: number | null = null;
  dropdownTop = 0;
  dropdownLeft = 0;

  // simulazione diverse chat
  chatTitles: string[] = [
    'Prenotazione stanza',
    'Supporto clienti',
    'Help Desk',
    'Ordine prodotto',
    'Aggiornamento spedizione',
    'Appuntamento medico',
    'Check-in hotel',
    'Risoluzione problemi',
    'Conferma prenotazione',
    'Pagamenti e fatture',
    'Promozioni e offerte',
    'Resi e rimborsi',
    'Riunione progetto',
    'Task e attività',
    'Annunci aziendali',
    'Brainstorming team',
    'Chat familiare',
    'Gruppo amici',
    'Suggerimenti',
    'Domande frequenti'
  ];

  openDrawer() {
    const el = this.drawer.nativeElement;
    el.classList.remove('-translate-x-full');
  }

  closeDrawer() {
    const el = this.drawer.nativeElement;
    el.classList.add('-translate-x-full');
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
}
