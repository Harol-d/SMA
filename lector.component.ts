import { Component, OnInit, ChangeDetectorRef, Output, EventEmitter} from '@angular/core';
import { interval, Subscription } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { IonInput, IonButton } from '@ionic/angular';
import { FormsModule,FormBuilder,FormGroup, Validators } from '@angular/forms';
import {DatosEmergencia} from '../../data/interfaces/datos-emergencia.model'

@Component({
  selector: 'app-lector',
  templateUrl: './lector.component.html',
  styleUrls: ['./lector.component.scss'],
  standalone:true,
  imports: [IonInput, IonButton, FormsModule]
})
export class LectorComponent implements OnInit {
  codUid: string= "";
  lecturas: Subscription;
  ipLector: string= "http://florence-lector.local"
  noPac: string = "";
  http: HttpClient;
  actualizar: ChangeDetectorRef;
  form: FormGroup;

  @Output() pacEncontrado = new EventEmitter();

  constructor(private fb: FormBuilder,pet: HttpClient, detec: ChangeDetectorRef) {
    this.http= pet;
    this.actualizar= detec;
  }

  ngOnInit() {
    this.form = this.fb.group({
      codUid: ['',[Validators.required]]
    })
    this.lecturas= interval(100).subscribe(()=>{this.leerPulsera();})
  }
  leerPulsera(){
    this.http.get(this.ipLector).subscribe((res:{uid:string})=>{
      this.codUid= res.uid;
      this.actualizar.detectChanges();
    })
  }

  buscar() {
    let api = `http://127.0.0.1:8000/pacientes/${this.codUid}`;

    if(!this.form.valid){
      this.form.markAllAsTouched();
    }
    this.http.get(api).subscribe(
      (res: DatosEmergencia) => {
        this.noPac = "";
        this.pacEncontrado.emit(res);
      () => {
        this.noPac = "PACIENTE NO SE ENCUENTRA EN EL SISTEMA";
        this.pacEncontrado.emit(null);
      }
    });
  }
}
