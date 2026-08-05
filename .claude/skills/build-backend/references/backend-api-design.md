# Backend API Design

A working reference for shaping RESTful, GraphQL, and gRPC APIs — the conventions worth keeping (2025).

## REST API Design

### Resource-Based URLs

Name URLs after the things they expose, not the actions you take on them. Nouns, not verbs.

**Do this:**
```
GET    /api/v1/users              # List users
GET    /api/v1/users/:id          # Get specific user
POST   /api/v1/users              # Create user
PUT    /api/v1/users/:id          # Update user (full)
PATCH  /api/v1/users/:id          # Update user (partial)
DELETE /api/v1/users/:id          # Delete user

GET    /api/v1/users/:id/posts    # Get user's posts
POST   /api/v1/users/:id/posts    # Create post for user
```

**Steer clear of:**
```
GET /api/v1/getUser?id=123        # RPC-style, not RESTful
POST /api/v1/createUser           # Verb in URL
GET /api/v1/user-posts            # Unclear relationship
```

### HTTP Status Codes (Meaningful Responses)

The status code is the first thing a caller reads. Pick the one that tells the truth about what happened.

**Success:**
- `200 OK` — the GET, PUT, or PATCH went through
- `201 Created` — the POST landed and a resource now exists
- `204 No Content` — the DELETE worked, nothing to send back

**Client Errors:**
- `400 Bad Request` — the input didn't pass muster
- `401 Unauthorized` — no credentials, or the ones given are bad
- `403 Forbidden` — they're signed in but not allowed here
- `404 Not Found` — the thing you asked for isn't here
- `409 Conflict` — it clashes with what's already there (duplicate email)
- `422 Unprocessable Entity` — validation failed, with the specifics
- `429 Too Many Requests` — you've tripped the rate limit

**Server Errors:**
- `500 Internal Server Error` — something broke on our side
- `502 Bad Gateway` — the upstream service answered badly
- `503 Service Unavailable` — down for the moment
- `504 Gateway Timeout` — the upstream service never replied in time

### Request/Response Format

**Request:**
```typescript
POST /api/v1/users
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "John Doe",
  "age": 30
}
```

**Success Response:**
```typescript
HTTP/1.1 201 Created
Content-Type: application/json
Location: /api/v1/users/123

{
  "id": "123",
  "email": "user@example.com",
  "name": "John Doe",
  "age": 30,
  "createdAt": "2025-01-09T12:00:00Z",
  "updatedAt": "2025-01-09T12:00:00Z"
}
```

**Error Response:**
```typescript
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format",
        "value": "invalid-email"
      },
      {
        "field": "age",
        "message": "Age must be between 18 and 120",
        "value": 15
      }
    ],
    "timestamp": "2025-01-09T12:00:00Z",
    "path": "/api/v1/users"
  }
}
```

### Pagination

```typescript
// Request
GET /api/v1/users?page=2&limit=50

// Response
{
  "data": [...],
  "pagination": {
    "page": 2,
    "limit": 50,
    "total": 1234,
    "totalPages": 25,
    "hasNext": true,
    "hasPrev": true
  },
  "links": {
    "first": "/api/v1/users?page=1&limit=50",
    "prev": "/api/v1/users?page=1&limit=50",
    "next": "/api/v1/users?page=3&limit=50",
    "last": "/api/v1/users?page=25&limit=50"
  }
}
```

### Filtering and Sorting

```
GET /api/v1/users?status=active&role=admin&sort=-createdAt,name&limit=20

# Filters: status=active AND role=admin
# Sort: createdAt DESC, name ASC
# Limit: 20 results
```

### API Versioning Strategies

**URL Versioning (Most Common):**
```
/api/v1/users
/api/v2/users
```

**Header Versioning:**
```
GET /api/users
Accept: application/vnd.myapi.v2+json
```

**Query Parameter:**
```
/api/users?version=2
```

**The trade-off:** URL versioning wins on plain visibility — anyone reading a log or a curl command sees the version. Reach for it unless you have a specific reason not to.

## GraphQL API Design

### Schema Definition

```graphql
type User {
  id: ID!
  email: String!
  name: String!
  posts: [Post!]!
  createdAt: DateTime!
}

type Post {
  id: ID!
  title: String!
  content: String!
  author: User!
  published: Boolean!
  createdAt: DateTime!
}

type Query {
  user(id: ID!): User
  users(limit: Int = 50, offset: Int = 0): [User!]!
  post(id: ID!): Post
  posts(authorId: ID, published: Boolean): [Post!]!
}

type Mutation {
  createUser(input: CreateUserInput!): User!
  updateUser(id: ID!, input: UpdateUserInput!): User!
  deleteUser(id: ID!): Boolean!

  createPost(input: CreatePostInput!): Post!
  publishPost(id: ID!): Post!
}

input CreateUserInput {
  email: String!
  name: String!
  password: String!
}

input UpdateUserInput {
  email: String
  name: String
}
```

### Queries

```graphql
# Flexible data fetching - client specifies exactly what they need
query {
  user(id: "123") {
    id
    name
    email
    posts {
      id
      title
      published
    }
  }
}

# With variables
query GetUser($userId: ID!) {
  user(id: $userId) {
    id
    name
    posts(published: true) {
      title
    }
  }
}
```

### Mutations

```graphql
mutation CreateUser($input: CreateUserInput!) {
  createUser(input: $input) {
    id
    email
    name
    createdAt
  }
}

# Variables
{
  "input": {
    "email": "user@example.com",
    "name": "John Doe",
    "password": "SecurePass123!"
  }
}
```

### Resolvers (NestJS Example)

```typescript
@Resolver(() => User)
export class UserResolver {
  constructor(
    private userService: UserService,
    private postService: PostService,
  ) {}

  @Query(() => User, { nullable: true })
  async user(@Args('id') id: string) {
    return this.userService.findById(id);
  }

  @Query(() => [User])
  async users(
    @Args('limit', { defaultValue: 50 }) limit: number,
    @Args('offset', { defaultValue: 0 }) offset: number,
  ) {
    return this.userService.findAll({ limit, offset });
  }

  @Mutation(() => User)
  async createUser(@Args('input') input: CreateUserInput) {
    return this.userService.create(input);
  }

  // Field resolver - lazy load posts
  @ResolveField(() => [Post])
  async posts(@Parent() user: User) {
    return this.postService.findByAuthorId(user.id);
  }
}
```

### GraphQL Best Practices

1. **Kill the N+1 query** — batch with DataLoader instead of firing one query per parent
```typescript
import DataLoader from 'dataloader';

const postLoader = new DataLoader(async (authorIds: string[]) => {
  const posts = await db.posts.findAll({ where: { authorId: authorIds } });
  return authorIds.map(id => posts.filter(p => p.authorId === id));
});

// In resolver
@ResolveField(() => [Post])
async posts(@Parent() user: User) {
  return this.postLoader.load(user.id);
}
```

2. **Pagination** — walk pages by Relay-style cursor, not raw offsets
3. **Error Handling** — fold errors into the response payload rather than swallowing them
4. **Depth Limiting** — put a ceiling on how far a query may nest
5. **Query Complexity Analysis** — turn away queries that cost too much to resolve

## gRPC API Design

### Protocol Buffers Schema

```protobuf
syntax = "proto3";

package user;

service UserService {
  rpc GetUser (GetUserRequest) returns (User);
  rpc ListUsers (ListUsersRequest) returns (ListUsersResponse);
  rpc CreateUser (CreateUserRequest) returns (User);
  rpc UpdateUser (UpdateUserRequest) returns (User);
  rpc DeleteUser (DeleteUserRequest) returns (DeleteUserResponse);

  // Streaming
  rpc StreamUsers (StreamUsersRequest) returns (stream User);
}

message User {
  string id = 1;
  string email = 2;
  string name = 3;
  int64 created_at = 4;
}

message GetUserRequest {
  string id = 1;
}

message ListUsersRequest {
  int32 limit = 1;
  int32 offset = 2;
}

message ListUsersResponse {
  repeated User users = 1;
  int32 total = 2;
}

message CreateUserRequest {
  string email = 1;
  string name = 2;
  string password = 3;
}
```

### Implementation (Node.js)

```typescript
import * as grpc from '@grpc/grpc-js';
import * as protoLoader from '@grpc/proto-loader';

const packageDefinition = protoLoader.loadSync('user.proto');
const userProto = grpc.loadPackageDefinition(packageDefinition).user;

// Server implementation
const server = new grpc.Server();

server.addService(userProto.UserService.service, {
  async getUser(call, callback) {
    const user = await userService.findById(call.request.id);
    callback(null, user);
  },

  async createUser(call, callback) {
    const user = await userService.create(call.request);
    callback(null, user);
  },

  async streamUsers(call) {
    const users = await userService.findAll();
    for (const user of users) {
      call.write(user);
    }
    call.end();
  },
});

server.bindAsync(
  '0.0.0.0:50051',
  grpc.ServerCredentials.createInsecure(),
  () => server.start()
);
```

### gRPC Benefits

- **Performance:** binary protocol runs 7-10x faster than REST
- **Streaming:** data flows both directions at once
- **Type Safety:** the schema is the contract — Protocol Buffers enforce types
- **Code Generation:** clients and servers generate straight from the proto
- **Best For:** service-to-service traffic inside your own walls, latency-sensitive workloads

## API Design Decision Matrix

| Feature | REST | GraphQL | gRPC |
|---------|------|---------|------|
| **Use Case** | Public APIs, CRUD | Client picks its own fields | Microservices, performance |
| **Performance** | Middle of the road | Middle of the road | Quickest (7-10x REST) |
| **Caching** | Rides on HTTP caching | Fiddly | Nothing built in |
| **Browser Support** | Works as-is | Works as-is | Needs gRPC-Web |
| **Learning Curve** | Gentle | Middling | Uphill |
| **Streaming** | Thin (SSE only) | Subscriptions | Both directions |
| **Tooling** | Top-shelf | Top-shelf | Decent |
| **Documentation** | OpenAPI/Swagger | Schema introspection | Protobuf definition |

## API Security Checklist

- [ ] HTTPS/TLS everywhere — never serve plain HTTP
- [ ] Authentication wired up (OAuth 2.1, JWT, API keys)
- [ ] Authorization enforced (RBAC, verify permissions per request)
- [ ] Rate limiting in place to blunt abuse
- [ ] Every endpoint validates its input
- [ ] CORS scoped to the origins you actually trust
- [ ] Security headers set (CSP, HSTS, X-Frame-Options)
- [ ] API versioning in place
- [ ] Errors stay quiet about internals — no stack traces, no system detail
- [ ] Audit trail recorded — who did what, and when

## API Documentation

### OpenAPI/Swagger (REST)

```yaml
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0
paths:
  /api/v1/users:
    get:
      summary: List users
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 50
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/User'
components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
        email:
          type: string
        name:
          type: string
```

## Resources

- **REST Best Practices:** https://restfulapi.net/
- **GraphQL:** https://graphql.org/learn/
- **gRPC:** https://grpc.io/docs/
- **OpenAPI:** https://swagger.io/specification/
