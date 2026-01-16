/**
 * MONGO MANAGER - SIMPLIFIED
 * --------------------------
 * Vereenvoudigde MongoDB manager zonder smart functies.
 * Rechtstreekse toegang tot DataGateway functies.
 */

class DataGateway {
    constructor(baseUrl, clientId, appName) {
        this.baseUrl = baseUrl;
        this.clientId = clientId;
        this.appName = appName;
    }

    _getUrl(collectionName, id = null) {
        let url = `${this.baseUrl}/api/${this.appName}_${collectionName}`;
        if (id) url += `/${id}`;
        return url;
    }

    async getCollection(name) {
        const response = await fetch(this._getUrl(name), {
            headers: { 'x-client-id': this.clientId }
        });
        if (!response.ok) throw new Error(`Server error: ${response.status}`);
        return await response.json();
    }

    async getDocument(name, id) {
        const response = await fetch(this._getUrl(name, id), {
            headers: { 'x-client-id': this.clientId }
        });
        if (!response.ok) {
            if (response.status === 404) return null;
            throw new Error(`Server error: ${response.status}`);
        }
        return await response.json();
    }

    async postDocument(name, data) {
        const response = await fetch(this._getUrl(name), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'x-client-id': this.clientId },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error(`POST error: ${response.status}`);
        return await response.json();
    }

    async putDocument(name, id, data) {
        const response = await fetch(this._getUrl(name, id), {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'x-client-id': this.clientId },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error(`PUT error: ${response.status}`);
        return await response.json();
    }

    async deleteDocument(name, id) {
        const response = await fetch(this._getUrl(name, id), {
            method: 'DELETE',
            headers: { 'x-client-id': this.clientId }
        });
        if (!response.ok) throw new Error(`DELETE error: ${response.status}`);
        return await response.json();
    }
}

class MongoManager {
    constructor(baseUrl, clientId, appName) {
        this.appName = appName;
        this.gateway = new DataGateway(baseUrl, clientId, appName);

        // Properties voor compatibiliteit met OfflineManager
        this.isSyncing = false;
        this.onSyncChange = null;
        this.onDataChanged = null;
        this.isOfflineSimulated = false;
    }

    // Direct gateway access - no smart functions
    async getCollection(collectionName) {
        return await this.gateway.getCollection(collectionName);
    }

    async getDocument(collectionName, id) {
        return await this.gateway.getDocument(collectionName, id);
    }

    async postDocument(collectionName, data) {
        return await this.gateway.postDocument(collectionName, data);
    }

    async putDocument(collectionName, id, data) {
        return await this.gateway.putDocument(collectionName, id, data);
    }

    async deleteDocument(collectionName, id) {
        return await this.gateway.deleteDocument(collectionName, id);
    }
}

