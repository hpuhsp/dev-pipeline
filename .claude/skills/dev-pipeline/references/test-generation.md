# Test Generation Guidelines

根据变更代码自动生成单元测试的指南。覆盖 JavaScript/TypeScript、Python、Java/Kotlin。

> **Token-efficient loading**: This file covers 4 language ecosystems. When loading, **read only the section matching the detected tech stack** from Phase 0 framework detection. Skip unrelated language sections.

## 通用原则

### 测试什么
1. **正常路径 (Happy Path)**：给定合法输入，产生预期输出
2. **边界条件 (Edge Cases)**：空值、零值、极值、空集合
3. **错误路径 (Error Path)**：非法输入、网络失败、超时、权限拒绝
4. **行为契约 (Contract)**：函数对外承诺的行为必须被验证

### 不测试什么
- 第三方库的内部行为（库已有自己的测试）
- 简单的 getter/setter（无逻辑的赋值语句）
- 框架的样板代码（如路由注册、配置加载）
- 纯数据结构的构造/解构

### 测试结构：AAA 模式

```
Arrange   → 准备测试数据和依赖
Act       → 执行被测试的代码
Assert    → 验证行为符合预期
```

### 命名规范

| 风格 | 格式 | 适用 |
|------|------|------|
| should | `should_returnX_whenY` | JS/TS 推荐 |
| test_ | `test_<function>_<scenario>` | Python 推荐 |
| given-when-then | `givenX_whenY_thenZ` | Java 推荐 |

---

## JavaScript/TypeScript

### 框架检测
检查 `package.json` 中是否有 `jest`、`vitest`、`mocha`、`@jest/globals`。
优先使用项目已有的框架，不要引入新框架。

### 模式示例

```typescript
// 测试纯函数
describe('calculateDiscount', () => {
  it('should apply 10% discount for orders above $100', () => {
    const result = calculateDiscount({ total: 150, customerType: 'regular' });
    expect(result).toBe(135);
  });

  it('should return original price when total is below threshold', () => {
    const result = calculateDiscount({ total: 50, customerType: 'regular' });
    expect(result).toBe(50);
  });

  it('should throw for negative total', () => {
    expect(() => calculateDiscount({ total: -10, customerType: 'regular' }))
      .toThrow('Total must be positive');
  });
});
```

```typescript
// 测试异步函数
describe('fetchUser', () => {
  it('should return user data when API call succeeds', async () => {
    // Arrange
    jest.spyOn(global, 'fetch').mockResolvedValue({
      json: () => Promise.resolve({ id: 1, name: 'Alice' })
    } as Response);

    // Act
    const user = await fetchUser(1);

    // Assert
    expect(user.name).toBe('Alice');
  });

  it('should throw FetchError when API call fails', async () => {
    jest.spyOn(global, 'fetch').mockRejectedValue(new Error('Network error'));
    await expect(fetchUser(1)).rejects.toThrow('Network error');
  });
});
```

```typescript
// 测试 React Hook
import { renderHook, act } from '@testing-library/react';

describe('useCounter', () => {
  it('should increment count', () => {
    const { result } = renderHook(() => useCounter(0));
    act(() => { result.current.increment(); });
    expect(result.current.count).toBe(1);
  });
});
```

### Mock 原则
- 在单元测试中 Mock 外部依赖（API、DB、文件系统）
- 不要 Mock 被测试模块内部的私有函数
- 测试实现在集成测试中运行，不在单元测试中

---

## Python

### 框架检测
检查 `pyproject.toml`、`setup.cfg`、`tox.ini` 或 `requirements-dev.txt` 中的 `pytest`、`unittest`。
检查项目根目录是否有 `pytest.ini`、`conftest.py`、`tox.ini`。

### 模式示例

```python
import pytest
from src.user_service import create_user, UserExistsError

class TestCreateUser:
    def test_creates_user_with_valid_input(self, db_session):
        """正常创建用户"""
        user = create_user(db_session, email="test@example.com", name="Alice")
        assert user.email == "test@example.com"
        assert user.name == "Alice"
        assert user.id is not None

    def test_raises_error_for_duplicate_email(self, db_session):
        """重复 email 应抛出异常"""
        create_user(db_session, email="test@example.com", name="Alice")
        with pytest.raises(UserExistsError, match="email already exists"):
            create_user(db_session, email="test@example.com", name="Bob")

    def test_rejects_invalid_email(self, db_session):
        """无效 email 格式应抛出 ValueError"""
        with pytest.raises(ValueError, match="invalid email"):
            create_user(db_session, email="not-an-email", name="Alice")

    @pytest.mark.parametrize("email", [
        "",
        None,
        "a" * 300,
    ])
    def test_rejects_edge_case_emails(self, db_session, email):
        with pytest.raises(ValueError):
            create_user(db_session, email=email, name="Alice")
```

### Fixture 使用

```python
@pytest.fixture
def db_session():
    """创建测试数据库会话，测试后回滚"""
    session = create_test_session()
    yield session
    session.rollback()
    session.close()
```

### Mock 使用

```python
from unittest.mock import patch, MagicMock

def test_sends_notification_on_create(db_session):
    with patch("src.user_service.send_email") as mock_send:
        create_user(db_session, email="a@b.com", name="Alice")
        mock_send.assert_called_once_with(
            to="a@b.com",
            subject="Welcome",
        )
```

---

## Java/Kotlin

### 框架检测
检查 `pom.xml` 或 `build.gradle` 中的：
- JUnit 5 (`junit-jupiter`)、JUnit 4 (`junit`)
- Mockito (`mockito-core`)
- AssertJ (`assertj-core`)
- TestNG (`testng`)

优先使用 JUnit 5 + Mockito + AssertJ 组合。

### 模式示例 (Java)

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository repository;

    @Mock
    private EmailSender emailSender;

    @InjectMocks
    private UserService userService;

    @Test
    void shouldCreateUserWithValidInput() {
        // Arrange
        CreateUserRequest request = new CreateUserRequest("alice@example.com", "Alice");
        when(repository.existsByEmail("alice@example.com")).thenReturn(false);
        when(repository.save(any(User.class)))
            .thenReturn(new User(1L, "alice@example.com", "Alice"));

        // Act
        User user = userService.createUser(request);

        // Assert
        assertThat(user.getId()).isEqualTo(1L);
        assertThat(user.getEmail()).isEqualTo("alice@example.com");
        verify(emailSender).sendWelcomeEmail("alice@example.com");
    }

    @Test
    void shouldThrowWhenEmailAlreadyExists() {
        CreateUserRequest request = new CreateUserRequest("alice@example.com", "Alice");
        when(repository.existsByEmail("alice@example.com")).thenReturn(true);

        assertThrows(UserExistsException.class, () -> userService.createUser(request));
    }

    @Test
    void shouldRejectNullEmail() {
        CreateUserRequest request = new CreateUserRequest(null, "Alice");
        assertThrows(IllegalArgumentException.class, () -> userService.createUser(request));
    }
}
```

### Kotlin

```kotlin
class UserServiceTest {
    private val repository = mockk<UserRepository>()
    private val emailSender = mockk<EmailSender>(relaxed = true)
    private val userService = UserService(repository, emailSender)

    @Test
    fun `should create user with valid input`() {
        every { repository.existsByEmail("alice@example.com") } returns false
        every { repository.save(any()) } returns User(1L, "alice@example.com", "Alice")

        val user = userService.createUser(CreateUserRequest("alice@example.com", "Alice"))

        assertThat(user.id).isEqualTo(1L)
        verify { emailSender.sendWelcomeEmail("alice@example.com") }
    }

    @Test
    fun `should throw when email already exists`() {
        every { repository.existsByEmail("alice@example.com") } returns true

        assertThrows<UserExistsException> {
            userService.createUser(CreateUserRequest("alice@example.com", "Alice"))
        }
    }
}
```

---

## Swift / iOS

### Framework Detection

1. `*.xcodeproj` / `*.xcworkspace` — XCTest（内置）
2. `Package.swift` — Swift Package Manager + XCTest
3. `Podfile` 中检查 `Quick`/`Nimble` — BDD 风格
4. 检查 test target 中 `*Tests.swift` 文件

### Pattern Examples

```swift
import XCTest
@testable import MyModule

final class UserServiceTests: XCTestCase {
    var sut: UserService!
    var mockNetwork: MockNetworkClient!

    override func setUp() {
        super.setUp()
        mockNetwork = MockNetworkClient()
        sut = UserService(network: mockNetwork)
    }

    override func tearDown() {
        sut = nil
        mockNetwork = nil
        super.tearDown()
    }

    func testCreateUserWithValidInputReturnsUser() {
        // Arrange
        let request = CreateUserRequest(email: "alice@example.com", name: "Alice")

        // Act
        let result = try? sut.createUser(request)

        // Assert
        XCTAssertNotNil(result)
        XCTAssertEqual(result?.email, "alice@example.com")
    }

    func testCreateUserWithDuplicateEmailThrowsError() {
        // Arrange
        mockNetwork.stubbedEmailExists = true
        let request = CreateUserRequest(email: "existing@example.com", name: "Bob")

        // Act & Assert
        XCTAssertThrowsError(try sut.createUser(request)) { error in
            guard let serviceError = error as? UserServiceError else {
                return XCTFail("Unexpected error type")
            }
            XCTAssertEqual(serviceError, .userAlreadyExists)
        }
    }

    func testFetchUserAsync() async throws {
        // Arrange
        let expectedUser = User(email: "alice@example.com", name: "Alice")
        mockNetwork.stubbedUser = expectedUser

        // Act
        let user = try await sut.fetchUser(email: "alice@example.com")

        // Assert
        XCTAssertEqual(user.name, "Alice")
    }
}
```

---

## 测试文件放置约定

| 语言 | 源文件 | 测试文件 |
|------|--------|----------|
| JS/TS (Jest) | `src/utils/math.ts` | `src/utils/__tests__/math.test.ts` 或 `src/utils/math.test.ts` |
| JS/TS (Vitest) | `src/utils/math.ts` | `src/utils/math.test.ts` 或 `tests/math.test.ts` |
| Python (pytest) | `src/models/user.py` | `tests/test_user.py` 或 `tests/models/test_user.py` |
| Java (JUnit) | `src/main/java/com/x/User.java` | `src/test/java/com/x/UserTest.java` |
| Kotlin (JUnit) | `src/main/kotlin/com/x/User.kt` | `src/test/kotlin/com/x/UserTest.kt` |
| Swift/XCTest | `Sources/Services/UserService.swift` | `Tests/Services/UserServiceTests.swift` |

## 运行测试

生成测试后，使用项目已有命令运行测试确保通过：
- JS/TS: `npm test` / `npx jest` / `npx vitest run`
- Python: `pytest` / `python -m pytest` / `tox`
- Java: `mvn test` / `gradle test`
- Swift: `xcodebuild test -scheme MyScheme` / `swift test`（SPM）

### Regression Test Identification · 回归测试识别

**If CodeGraph is available** (`codegraph_available = true`) · CodeGraph 可用时:

- Run `git diff HEAD --name-only | codegraph affected --stdin --quiet` to get the precise list of impacted test files from both staged and unstaged changes
- Run those specific test files to check for regressions:
  - JS/TS: `npx jest --testPathPattern "auth|user"` (or pipe affected files directly)
  - Python: `pytest tests/test_auth.py tests/test_user.py`
  - Java: `mvn test -Dtest=AuthServiceTest,UserServiceTest`
- This is more precise than module scoping — only tests whose dependencies changed are executed

**If CodeGraph is not available** · CodeGraph 不可用时:

- Fall back to module/package scoping: `pytest tests/auth/`, `npm test -- --testPathPattern auth`
- Use `git ls-files '*test*' '*spec*' '*__tests__*'` to discover existing test files in changed areas
