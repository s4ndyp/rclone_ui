/**
 * MONGO MANAGER - DIRECT ONLINE (NO DEXIE)
 * ----------------------------------------
 * Vervanging voor OfflineManager voor web apps die altijd online zijn.
 * Bevat dezelfde functie-signaturen voor eenvoudige uitwisselbaarheid.
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

    async saveDocument(name, data) {
        let method = data._id ? 'PUT' : 'POST';
        let url = this._getUrl(name, data._id);
        
        try {
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json', 'x-client-id': this.clientId },
                body: JSON.stringify(data)
            });

            // If PUT fails with 404, it means the record with manual _id doesn't exist yet.
            // In that case, we should try a POST to create it.
            if (!response.ok && response.status === 404 && method === 'PUT') {
                const postUrl = this._getUrl(name);
                const postResponse = await fetch(postUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'x-client-id': this.clientId },
                    body: JSON.stringify(data)
                });
                if (!postResponse.ok) throw new Error(`Save (POST fallback) error: ${postResponse.status}`);
                return await postResponse.json();
            }

            if (!response.ok) throw new Error(`Save error: ${response.status}`);
            return await response.json();
        } catch (e) {
            console.error("Gateway saveDocument error:", e);
            throw e;
        }
    }

    async deleteDocument(name, id) {
        const response = await fetch(this._getUrl(name, id), {
            method: 'DELETE',
            headers: { 'x-client-id': this.clientId }
        });
        if (!response.ok) throw new Error(`Delete error: ${response.status}`);
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

    /**
     * Slaat direct op naar de server.
     */
    async saveSmartDocument(collectionName, data) {
        // Direct doorsturen naar gateway
        const result = await this.gateway.saveDocument(collectionName, data);
        
        // Trigger update event voor UI
        if (this.onDataChanged) this.onDataChanged(collectionName);
        
        return result;
    }

    async deleteSmartDocument(collectionName, id) {
        await this.gateway.deleteDocument(collectionName, id);
        
        // Trigger update event voor UI
        if (this.onDataChanged) this.onDataChanged(collectionName);
    }

    /**
     * Haalt data direct van de server.
     */
    async getSmartCollection(collectionName) {
        return await this.gateway.getCollection(collectionName);
    }

    /**
     * In OfflineManager haalt dit data van server naar cache.
     * Hier is geen cache, dus we triggeren alleen een UI refresh 
     * zodat de app getSmartCollection opnieuw aanroept.
     */
    async refreshCache(collectionName) {
        if (this.onDataChanged) this.onDataChanged(collectionName);
    }
}

