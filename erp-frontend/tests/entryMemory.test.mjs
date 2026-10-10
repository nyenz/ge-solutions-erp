// fix188: the data entry helper rules. Run with `npm test`.
import test from 'node:test';
import assert from 'node:assert/strict';
import { buildPlaces, suggestPlace, matchRank, editDistance, nearMiss, placeValues, buildPeople, suggestPeople, suggestForRow, suggestValues, norm } from '../src/utils/entryMemory.js';

const P = (district, county, subCounty, parish, village) => ({ district, county, subCounty, parish, village });
const projects = [
    P('Jinja', 'Butembe', 'Mafubira', 'Buwenda', 'Namulesa'),
    P('JINJA', 'BUTEMBE', 'MAFUBIRA', 'BUWENDA', ' namulesa '),       // same place, written differently
    P('Jinja', 'Butembe', 'Mafubira', 'Buwenda', 'Wakitaka'),
    P('Iganga', 'Kigulu', 'Nakalama', 'Bukoyo', 'Nabidongha'),
    P('Kamuli', 'Bugabula', 'Namwendwa', 'Kinu', 'Bulogo'),
    P('Mayuge', 'Bunya', 'Imanyiro', 'Magada', 'Bulogo'),             // the same village name in two districts
    { district: '', village: '' }, null,
];
const places = buildPlaces(projects);

test('places are counted once however they were typed', () => {
    assert.equal(places.length, 5);
    assert.equal(places.find(p => p.village === 'NAMULESA').count, 2);
    assert.equal(norm('  jinja   east '), 'JINJA EAST');
});

test('typing a village offers the rest of the location in one pick', () => {
    const s = suggestPlace(places, 'village', 'namu');
    assert.equal(s[0].value, 'NAMULESA');
    assert.deepEqual(s[0].fill, { district: 'JINJA', county: 'BUTEMBE', subCounty: 'MAFUBIRA', parish: 'BUWENDA' });
    assert.equal(s[0].detail, 'BUWENDA / MAFUBIRA / BUTEMBE / JINJA');
});

test('a village name used in two districts fills nothing it cannot be sure of', () => {
    const s = suggestPlace(places, 'village', 'bulo');
    assert.equal(s.length, 1);
    assert.deepEqual(s[0].fill, {});                       // Kamuli or Mayuge? the person must say
    assert.deepEqual(suggestPlace(places, 'village', 'bulogo'), []);   // typed in full and nothing sure to add: no list
    // once the district is filled the answer is clear again
    const k = suggestPlace(places, 'village', 'bul', { district: 'kamuli' });
    assert.equal(k[0].fill.parish, 'KINU');
    assert.equal(k[0].fill.district, 'KAMULI');
});

test('a filled parent box narrows the list; the most used value comes first', () => {
    assert.deepEqual(suggestPlace(places, 'village', '', { district: 'Jinja' }).map(s => s.value), ['NAMULESA', 'WAKITAKA']);
    assert.deepEqual(suggestPlace(places, 'district', 'k').map(s => s.value), ['KAMULI']);
    assert.deepEqual(suggestPlace(places, 'village', 'zzz'), []);
    assert.deepEqual(suggestPlace(places, 'nonsense', 'a'), []);
});

test('an exact match with nothing left to offer shows no list', () => {
    const ctx = { district: 'JINJA', county: 'BUTEMBE', subCounty: 'MAFUBIRA', parish: 'BUWENDA' };
    assert.deepEqual(suggestPlace(places, 'village', 'Namulesa', ctx), []);
    // but with the other boxes still empty the same word still offers to fill them
    assert.equal(suggestPlace(places, 'village', 'Namulesa').length, 1);
});

test('matching: start of the value, start of a later word, then anywhere', () => {
    assert.equal(matchRank('LAND BOARD FEES', 'land'), 0);
    assert.equal(matchRank('LAND BOARD FEES', 'boa'), 1);
    assert.equal(matchRank('LAND BOARD FEES', 'oard'), 2);
    assert.equal(matchRank('LAND BOARD FEES', 'xyz'), -1);
    assert.equal(matchRank('', 'a'), -1);
});

test('likely typos are caught, short words and known words are left alone', () => {
    const villages = placeValues(places, 'village');
    assert.equal(nearMiss(villages, 'Namulessa'), 'NAMULESA');     // one letter too many
    assert.equal(nearMiss(villages, 'Nabidonga'), 'NABIDONGHA');
    assert.equal(nearMiss(villages, 'Namulesa'), null);            // known
    assert.equal(nearMiss(villages, 'Bulo'), null);                // too short to judge
    assert.equal(nearMiss(villages, 'Kampala'), null);             // simply a new place
    assert.equal(editDistance('kitten', 'sitting'), 3);
    assert.equal(editDistance('same', 'SAME'), 0);
    assert.equal(editDistance('a', 'abcdefgh', 2), 3);             // stopped early
});

const people = buildPeople([
    { id: 1, name: 'Namiiro Michael', nin: 'CM90010000ABCD', phone: '+256772000000 / +256701000000', email: 'm@x.com' },
    { id: 2, name: 'Kawooya Henry', nin: 'CM91010137ABCD', phone: '+256773234567' },
    { id: 3, name: 'NAMIIRO MICHAEL', nin: 'cm90010000abcd', phone: 'x' },      // the same National ID again
    { id: 4, fullName: 'Nakato Sarah', nationalId: 'CF97010959ABCD', phoneNumber: '+256780641969' },
    null, {},
]);

test('people: one row per National ID, from either field naming', () => {
    assert.equal(people.length, 3);
    assert.equal(people[2].name, 'NAKATO SARAH');
});

test('people are suggested by name, National ID or phone, and never from one letter', () => {
    assert.deepEqual(suggestPeople(people, 'fullName', 'n'), []);
    assert.deepEqual(suggestPeople(people, 'fullName', 'na').length, 0);
    assert.deepEqual(suggestPeople(people, 'fullName', 'nam').map(s => s.value), ['NAMIIRO MICHAEL']);
    assert.deepEqual(suggestPeople(people, 'fullName', 'henry').map(s => s.person.nin), ['CM91010137ABCD']);
    assert.deepEqual(suggestPeople(people, 'nationalId', 'cm9').map(s => s.value), ['CM91010137ABCD', 'CM90010000ABCD']);   // by name: Kawooya, Namiiro
    assert.deepEqual(suggestPeople(people, 'phone', '0773 234').map(s => s.label), ['KAWOOYA HENRY']);
    assert.deepEqual(suggestPeople(people, 'phone', '07'), []);
    assert.equal(suggestPeople(people, 'fullName', 'nam')[0].detail, 'CM90010000ABCD  -  +256772000000 / +256701000000');
});

test('free text: most used first, the value already typed is not repeated', () => {
    const cats = ['Fuel', 'fuel', 'FUEL', 'Airtime', 'Land board fees', 'Lunch', ''];
    assert.deepEqual(suggestValues(cats, 'f').map(s => s.value), ['Fuel', 'Land board fees']);
    assert.deepEqual(suggestValues(cats, 'fuel'), []);
    assert.deepEqual(suggestValues(cats, '').map(s => s.value)[0], 'Fuel');
    assert.deepEqual(suggestValues(null, 'x'), []);
});

// fix199 (test note 20): a filled NIN offers its person first in the name and phone boxes
test('a row whose NIN is known offers that person in the other boxes', () => {
    const people = buildPeople([{ nationalId: 'CM86021104KJTA', fullName: 'Kato Samuel Wanyama', phoneNumber: '+256772418306' },
        { nationalId: 'CF91030577LMPE', fullName: 'Namukose Sarah', phoneNumber: '+256701593268' }]);
    const row = { nationalId: 'cm86021104kjta', fullName: '', phone: '' };
    assert.equal(suggestForRow(people, 'fullName', row)[0].value, 'KATO SAMUEL WANYAMA');
    assert.equal(suggestForRow(people, 'phone', row)[0].value, '+256772418306');
    const done = { nationalId: 'CM86021104KJTA', fullName: 'Kato Samuel Wanyama', phone: '+256772418306' };
    assert.equal(suggestForRow(people, 'fullName', done).length, 0, 'nothing to offer once the row is complete');
    assert.equal(suggestForRow(people, 'nationalId', { nationalId: '', fullName: 'KATO SAMUEL WANYAMA', phone: '' })[0].value, 'CM86021104KJTA');
});
