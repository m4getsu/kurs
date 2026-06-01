class Deferred {
    constructor() {
        this._state = 'pending';
        this._value = undefined;
        this._doneCallbacks = [];
        this._failCallbacks = [];
        this._alwaysCallbacks = [];
    }

    resolve(value) {
        if (this._state !== 'pending') return this;
        this._state = 'resolved';
        this._value = value;
        this._doneCallbacks.forEach(cb => cb(value));
        this._alwaysCallbacks.forEach(cb => cb(value));
        return this;
    }

    reject(reason) {
        if (this._state !== 'pending') return this;
        this._state = 'rejected';
        this._value = reason;
        this._failCallbacks.forEach(cb => cb(reason));
        this._alwaysCallbacks.forEach(cb => cb(reason));
        return this;
    }

    done(callback) {
        if (this._state === 'resolved') callback(this._value);
        else if (this._state === 'pending') this._doneCallbacks.push(callback);
        return this;
    }

    fail(callback) {
        if (this._state === 'rejected') callback(this._value);
        else if (this._state === 'pending') this._failCallbacks.push(callback);
        return this;
    }

    always(callback) {
        if (this._state !== 'pending') callback(this._value);
        else this._alwaysCallbacks.push(callback);
        return this;
    }

    then(onDone, onFail) {
        if (onDone) this.done(onDone);
        if (onFail) this.fail(onFail);
        return this;
    }
}

function ajaxDeferred(url, options = {}) {
    const deferred = new Deferred();
    fetch(url, options)
        .then(function (response) {
            if (response.status === 401) {
                deferred.reject({ status: 401 });
            } else if (!response.ok) {
                deferred.reject({ status: response.status });
            } else {
                return response.json().then(function (data) {
                    deferred.resolve(data);
                });
            }
        })
        .catch(function (err) {
            deferred.reject(err);
        });
    return deferred;
}
