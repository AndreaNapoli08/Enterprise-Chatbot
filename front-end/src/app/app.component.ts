import { Component } from '@angular/core';
import { RouterOutlet, Router, NavigationEnd } from '@angular/router';
import { OnInit } from '@angular/core';
import { initFlowbite } from 'flowbite';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
  standalone: true,
  imports: [RouterOutlet],
})
export class AppComponent implements OnInit {
  constructor(private router: Router) {}

  ngOnInit(): void {
    // aggiornamento colore scrollbar in base al tema (chiaro/scuro)
    const mq = window.matchMedia('(prefers-color-scheme: dark)');

    const applyTheme = (isDark: boolean) => {
      const html = document.documentElement;
      if (isDark) html.classList.add('dark');
      else html.classList.remove('dark');

      // 👇 forza il repaint (senza ricaricare la pagina)
      document.body.style.display = 'none';
      // forza il browser a ricalcolare lo stile
      void document.body.offsetHeight;
      document.body.style.display = '';
    };

    // Applica subito il tema
    applyTheme(mq.matches);

    // Ascolta cambiamenti in tempo reale
    mq.addEventListener('change', e => applyTheme(e.matches));

    initFlowbite();
    this.router.events.subscribe((event) => {
      if (event instanceof NavigationEnd) {
        initFlowbite();
      }
    });
  }
}