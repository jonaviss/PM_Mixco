// Frontend/js/api.js
const BASE_URL = 'http://127.0.0.1:8000';

const API = {
    post: async (endpoint, datos, requerirToken = false) => {
        const headers = { 'Content-Type': 'application/json' };
        if (requerirToken) {
            const token = localStorage.getItem('token');
            if (token) headers['Authorization'] = `Bearer ${token}`;
        }
        return await fetch(`${BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(datos)
        });
    },

    get: async (endpoint, requerirToken = true) => {
        const headers = {};
        if (requerirToken) {
            const token = localStorage.getItem('token');
            if (token) headers['Authorization'] = `Bearer ${token}`;
        }
        return await fetch(`${BASE_URL}${endpoint}`, {
            method: 'GET',
            headers: headers
        });
    }
};