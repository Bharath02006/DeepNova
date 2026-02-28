export const BAD_CODE_EXAMPLE = `function processUsers(users) {
  for (let i = 0; i < users.length; i++) {
    for (let j = 0; j < users.length; j++) {
      for (let k = 0; k < users.length; k++) {
        if (users[i].email === users[j].email && users[j].email === users[k].email) {
          console.log("duplicate", users[i].email);
        }
      }
    }
  }
}

// TODO: also call external API for each user
async function syncUsers(users) {
  for (const u of users) {
    await fetch("https://example.com/api/users", {
      method: "POST",
      body: JSON.stringify(u),
    });
  }
}
`;

export const GOOD_CODE_EXAMPLE = `function processUsers(users) {
  const seen = new Map();

  for (const user of users) {
    const count = seen.get(user.email) ?? 0;
    seen.set(user.email, count + 1);
  }

  for (const [email, count] of seen) {
    if (count > 1) {
      console.log("duplicate", email);
    }
  }
}

async function syncUsers(users) {
  const res = await fetch("https://example.com/api/bulk-users", {
    method: "POST",
    body: JSON.stringify(users),
  });

  if (!res.ok) {
    throw new Error("Failed to sync users");
  }
}
`;

