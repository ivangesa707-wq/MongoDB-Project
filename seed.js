// Gesaivan Market Management System - Database Seed Script (mongosh)
// Inserts sample data directly into MongoDB so it is visible in MongoDB Compass

const dbName = 'gesaivan_market';
const targetDb = db.getSiblingDB(dbName);

print(`Seeding database: ${dbName} ...`);

// Drop existing collections
['buyers', 'farmers', 'markets', 'price_listings', 'records'].forEach(col => {
  targetDb[col].drop();
});
print('Existing collections dropped.');

function utc(daysAgo = 0) {
  const d = new Date();
  d.setDate(d.getDate() - daysAgo);
  return d;
}

// 1. Buyers
const buyersRes = targetDb.buyers.insertMany([
  { name: "John Mukasa",    contact: "+256-700-111222", location: "Kampala",   created_at: utc(60) },
  { name: "Grace Namukasa", contact: "+256-772-333444", location: "Entebbe",   created_at: utc(55) },
  { name: "Peter Ochieng",  contact: "+256-752-555666", location: "Jinja",     created_at: utc(50) },
  { name: "Fatuma Hassan",  contact: "+256-704-777888", location: "Mbale",     created_at: utc(45) },
  { name: "David Ssempa",   contact: "+256-776-999000", location: "Mbarara",   created_at: utc(40) }
]);
const buyers = Object.values(buyersRes.insertedIds);
print(`  ${buyers.length} buyers inserted.`);

// 2. Farmers
const farmersRes = targetDb.farmers.insertMany([
  { name: "Sarah Nakato",    contact: "+256-700-100200", location: "Wakiso",    created_at: utc(80) },
  { name: "Robert Opio",     contact: "+256-772-300400", location: "Lira",      created_at: utc(75) },
  { name: "Agnes Atim",      contact: "+256-752-500600", location: "Gulu",      created_at: utc(70) },
  { name: "Hassan Kiggundu", contact: "+256-704-700800", location: "Masaka",    created_at: utc(65) },
  { name: "Mary Ayot",       contact: "+256-776-900100", location: "Soroti",    created_at: utc(60) }
]);
const farmers = Object.values(farmersRes.insertedIds);
print(`  ${farmers.length} farmers inserted.`);

// 3. Markets
const marketsRes = targetDb.markets.insertMany([
  { name: "Owino Market",     location: "Kampala Central",  description: "Uganda's largest open-air market. Trades all staple crops Mon–Sat.", created_at: utc(90) },
  { name: "St. Balikuddembe", location: "Kampala",          description: "Wholesale hub for vegetables, grains, and livestock products.",        created_at: utc(85) },
  { name: "Jinja Main Market", location: "Jinja",           description: "Eastern Uganda's primary agricultural trading centre.",                created_at: utc(80) },
  { name: "Gulu Market",      location: "Gulu",            description: "Major market serving northern Uganda farmers and buyers.",              created_at: utc(75) },
  { name: "Mbarara Market",   location: "Mbarara",         description: "South-west hub known for dairy, beef, and maize.",                     created_at: utc(70) }
]);
const markets = Object.values(marketsRes.insertedIds);
print(`  ${markets.length} markets inserted.`);

// 4. Price Listings
const products = [
  ["Maize",        1800, "kg",    0, 0],
  ["Beans",        3500, "kg",    1, 1],
  ["Tomatoes",     2200, "crate", 2, 2],
  ["Cassava",       800, "kg",    3, 3],
  ["Sorghum",      1600, "kg",    4, 4],
  ["Millet",       2000, "kg",    0, 1],
  ["Groundnuts",   4500, "kg",    1, 0],
  ["Sweet Potato",  600, "bag",   2, 2],
  ["Coffee",       7000, "kg",    3, 3],
  ["Banana",       1200, "bunch", 4, 4]
];

const listings = products.map(([prod, price, unit, fi, mi], i) => ({
  product: prod,
  price: price,
  unit: unit,
  farmer_id: farmers[fi],
  market_id: markets[mi],
  listing_date: utc(i * 3),
  created_at: utc(i * 3)
}));

const listingsRes = targetDb.price_listings.insertMany(listings);
print(`  ${Object.keys(listingsRes.insertedIds).length} price listings inserted.`);

// 5. Records
const txTypes = ["Sale", "Purchase", "Transfer", "Return", "Sale", "Sale"];
const records = [];
for (let i = 0; i < 12; i++) {
  const bi = i % buyers.length;
  const fi = i % farmers.length;
  const mi = i % markets.length;
  records.push({
    transaction_type: txTypes[i % txTypes.length],
    buyer_id:  buyers[bi],
    farmer_id: farmers[fi],
    product:   products[i % products.length][0],
    quantity:  (i + 1) * 5,
    price:     products[i % products.length][1],
    market_id: markets[mi],
    date:      utc(i * 4),
    notes:     `Seed record #${i + 1}`,
    created_at: utc(i * 4)
  });
}

const recordsRes = targetDb.records.insertMany(records);
print(`  ${Object.keys(recordsRes.insertedIds).length} records inserted.`);

print("\nSeeding complete! Check MongoDB Compass under database 'gesaivan_market'.");
