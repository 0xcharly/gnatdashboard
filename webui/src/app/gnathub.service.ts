import { Injectable } from '@angular/core';
import { Http, Response } from '@angular/http';
import { Observable } from 'rxjs/Observable';

import { IGNAThubReport, IGNAThubBlob } from 'gnat';

import 'rxjs/add/operator/map';
import 'rxjs/add/operator/catch';

@Injectable()
export class GNAThubService {
    constructor(private http: Http) {}

    getReport(): Observable<IGNAThubReport> {
        return this.http.get('data/gnathub.report.json')
                        .map(this.handleResults)
                        .catch(this.handleError);
    }

    getSource(filename): Observable<IGNAThubBlob> {
        return this.http.get(`data/src/${filename}.json`)
                        .map(this.handleResults)
                        .catch(this.handleError);
    }

    private handleResults(res: Response) {
        return res.json() || {};
    }

    private handleError(error: any) {
        let errMsg = (error.message) ?
            error.message : error.status ?
                `${error.status} - ${error.statusText}` : 'Server error';
        console.error(errMsg);
        return Observable.throw(errMsg);
    }
}