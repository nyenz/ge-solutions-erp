import { test } from 'node:test';
import assert from 'node:assert/strict';
import { keepsCase, toUpperValue } from '../src/utils/upperCase.js';

test('names and places become capitals', () => {
    assert.equal(toUpperValue('Namigadde Stella'), 'NAMIGADDE STELLA');
    assert.equal(toUpperValue('iganga east'), 'IGANGA EAST');
    assert.equal(toUpperValue('CM94500KLM'), null, 'already capitals: nothing to do');
});
test('e-mail and links are never changed', () => {
    assert.equal(toUpperValue('stella@mail.test'), null);
    assert.equal(toUpperValue('https://ges.ug'), null);
});
test('e-mail, user name, key, search and other kinds of boxes keep what was typed', () => {
    assert.equal(keepsCase({ type: 'email' }), true);
    assert.equal(keepsCase({ type: 'password' }), true);
    assert.equal(keepsCase({ type: 'search' }), true);
    assert.equal(keepsCase({ type: 'text', id: 'login-username' }), true);
    assert.equal(keepsCase({ type: 'text', ariaLabel: 'Email of client 1' }), true);
    assert.equal(keepsCase({ type: 'text', inKeepCase: true }), true);
    assert.equal(keepsCase({ type: 'text', placeholder: 'Bank reference' }), true);
    assert.equal(keepsCase({ type: 'text', ariaLabel: 'District' }), false);
    assert.equal(keepsCase({ type: null }), false, 'a box with no type is a text box');
});
