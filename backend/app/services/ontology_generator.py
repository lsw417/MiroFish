"""
온톨로지 생성 서비스
인터페이스1: 텍스트 내용을 분석하여 사회 시뮬레이션에 적합한 엔티티 및 관계 타입 정의를 생성
"""

import json
from typing import Dict, Any, List, Optional
from ..utils.llm_client import LLMClient


# 온톨로지 생성 시스템 프롬프트
ONTOLOGY_SYSTEM_PROMPT = """당신은 전문 지식 그래프 온톨로지 설계 전문가입니다. 주어진 텍스트 내용과 시뮬레이션 요구사항을 분석하여 **소셜 미디어 여론 시뮬레이션**에 적합한 엔티티 타입과 관계 타입을 설계하세요.

**중요: 반드시 유효한 JSON 형식의 데이터를 출력하세요. 다른 내용은 출력하지 마세요.**

## 핵심 작업 배경

우리는 **소셜 미디어 여론 시뮬레이션 시스템**을 구축하고 있습니다. 이 시스템에서:
- 모든 엔티티는 소셜 미디어에서 발언하고, 상호작용하며, 정보를 전파할 수 있는 "계정" 또는 "주체"입니다
- 엔티티들은 서로 영향을 주고, 리트윗·댓글·응답을 주고받습니다
- 여론 사건에서 각 주체의 반응과 정보 전파 경로를 시뮬레이션합니다

따라서, **엔티티는 현실에 실제로 존재하며, 소셜 미디어에서 발언하고 상호작용할 수 있는 주체여야 합니다**:

**가능한 엔티티**:
- 구체적인 개인 (공인, 당사자, 오피니언 리더, 전문가/학자, 일반인)
- 기업 (공식 계정 포함)
- 조직 기관 (대학, 협회, NGO, 노조 등)
- 정부 부처, 감독 기관
- 미디어 기관 (신문사, 방송국, 1인 미디어, 웹사이트)
- 소셜 미디어 플랫폼 자체
- 특정 집단 대표 (동문회, 팬클럽, 권리 운동 단체 등)

**불가능한 엔티티**:
- 추상 개념 (예: "여론", "감정", "트렌드")
- 주제/토픽 (예: "학문적 정직성", "교육 개혁")
- 관점/태도 (예: "지지 측", "반대 측")

## 출력 형식

아래 구조의 JSON 형식으로 출력하세요:

```json
{
    "entity_types": [
        {
            "name": "엔티티 타입명 (영문, PascalCase)",
            "description": "간략한 설명 (영문, 100자 이내)",
            "attributes": [
                {
                    "name": "속성명 (영문, snake_case)",
                    "type": "text",
                    "description": "속성 설명"
                }
            ],
            "examples": ["예시 엔티티1", "예시 엔티티2"]
        }
    ],
    "edge_types": [
        {
            "name": "관계 타입명 (영문, UPPER_SNAKE_CASE)",
            "description": "간략한 설명 (영문, 100자 이내)",
            "source_targets": [
                {"source": "출발 엔티티 타입", "target": "도착 엔티티 타입"}
            ],
            "attributes": []
        }
    ],
    "analysis_summary": "텍스트 내용에 대한 간략한 분석 요약 (한국어)"
}
```

## 설계 가이드 (매우 중요!)

### 1. 엔티티 타입 설계 - 반드시 엄수

**수량 요건: 정확히 10개의 엔티티 타입**

**계층 구조 요건 (구체 타입 + 기본 타입을 동시에 포함해야 함)**:

10개의 엔티티 타입은 다음 계층을 포함해야 합니다:

A. **기본(fallback) 타입 (필수 포함, 리스트 마지막 2개에 배치)**:
   - `Person`: 모든 자연인 개체의 기본 타입. 더 구체적인 인물 타입에 해당하지 않는 경우 여기에 분류.
   - `Organization`: 모든 조직/기관의 기본 타입. 더 구체적인 조직 타입에 해당하지 않는 경우 여기에 분류.

B. **구체 타입 (8개, 텍스트 내용 기반으로 설계)**:
   - 텍스트에 등장하는 주요 역할에 맞는 더 구체적인 타입을 설계
   - 예: 텍스트가 학술 사건을 다룬다면 `Student`, `Professor`, `University`
   - 예: 텍스트가 비즈니스 사건을 다룬다면 `Company`, `CEO`, `Employee`

**기본 타입이 필요한 이유**:
- 텍스트에는 "초등학교 교사", "지나가던 행인", "어느 네티즌" 등 다양한 인물이 등장합니다
- 특정 타입에 해당하지 않으면 `Person`으로 분류해야 합니다
- 마찬가지로, 소규모 조직, 임시 단체 등은 `Organization`으로 분류해야 합니다

**구체 타입 설계 원칙**:
- 텍스트에서 자주 등장하거나 핵심적인 역할 타입을 식별
- 각 구체 타입은 명확한 경계가 있어야 하며 중복 없도록
- description은 이 타입과 기본 타입의 차이를 명확히 설명해야 함

### 2. 관계 타입 설계

- 수량: 6~10개
- 관계는 소셜 미디어 상호작용에서의 실제 연결을 반영해야 함
- source_targets가 정의한 엔티티 타입을 포함하도록 확인

### 3. 속성 설계

- 엔티티 타입당 1~3개의 핵심 속성
- **주의**: 속성명에 `name`, `uuid`, `group_id`, `created_at`, `summary`는 사용 불가 (시스템 예약어)
- 권장 사용: `full_name`, `title`, `role`, `position`, `location`, `description` 등

### 4. 엔티티 이름 규범 (매우 중요!)

텍스트에서 엔티티 인스턴스를 추출할 때 이름은 다음 규칙을 준수해야 합니다:
- **완전한 공식 이름 또는 전체 성명 사용**: 예: "김민준" (O), "A씨", "학생A" (X)
- **기관의 공식 전체 명칭 사용**: 예: "서울대학교" (O), "해당 대학" (X)
- **역할명 대체 금지**: "교수", "담당자", "관계자"를 엔티티 이름으로 사용 불가
- **익명 코드명 금지**: "A교수", "B학생", "C기업" 등의 형식 사용 불가
- 텍스트에서 직함만 있고 이름이 없는 경우, "[직책] at [기관]" 형식 사용. 예: "총장 at 한국대학교"

## 엔티티 타입 참고

**개인 (구체)**:
- Student: 학생
- Professor: 교수/학자
- Journalist: 기자
- Celebrity: 연예인/인플루언서
- Executive: 임원/CEO
- Official: 정부 관리
- Lawyer: 변호사
- Doctor: 의사

**개인 (기본 fallback)**:
- Person: 모든 자연인 (위의 구체 타입에 해당하지 않을 때 사용)

**조직 (구체)**:
- University: 대학교
- Company: 기업
- GovernmentAgency: 정부 기관
- MediaOutlet: 미디어 기관
- Hospital: 병원
- School: 초중고등학교
- NGO: 비정부기구

**조직 (기본 fallback)**:
- Organization: 모든 조직/기관 (위의 구체 타입에 해당하지 않을 때 사용)

## 관계 타입 참고

- WORKS_FOR: ~에서 근무
- STUDIES_AT: ~에서 재학
- AFFILIATED_WITH: ~에 소속
- REPRESENTS: ~을 대표
- REGULATES: ~을 감독
- REPORTS_ON: ~을 보도
- COMMENTS_ON: ~에 댓글/논평
- RESPONDS_TO: ~에 응답
- SUPPORTS: ~을 지지
- OPPOSES: ~에 반대
- COLLABORATES_WITH: ~와 협력
- COMPETES_WITH: ~와 경쟁
"""


class OntologyGenerator:
    """
    온톨로지 생성기
    텍스트 내용을 분석하여 엔티티 및 관계 타입 정의를 생성
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    def generate(
        self,
        document_texts: List[str],
        simulation_requirement: str,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        온톨로지 정의 생성

        Args:
            document_texts: 문서 텍스트 목록
            simulation_requirement: 시뮬레이션 요구사항 설명
            additional_context: 추가 컨텍스트

        Returns:
            온톨로지 정의 (entity_types, edge_types 등)
        """
        # 사용자 메시지 구성
        user_message = self._build_user_message(
            document_texts,
            simulation_requirement,
            additional_context
        )

        messages = [
            {"role": "system", "content": ONTOLOGY_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]

        # LLM 호출
        result = self.llm_client.chat_json(
            messages=messages,
            temperature=0.3,
            max_tokens=8192
        )

        # 검증 및 후처리
        result = self._validate_and_process(result)

        return result

    # LLM에 전달하는 텍스트 최대 길이 (로컬 소형 모델 최적화: 8천자)
    MAX_TEXT_LENGTH_FOR_LLM = 8000

    def _build_user_message(
        self,
        document_texts: List[str],
        simulation_requirement: str,
        additional_context: Optional[str]
    ) -> str:
        """사용자 메시지 구성"""

        # 텍스트 합치기
        combined_text = "\n\n---\n\n".join(document_texts)
        original_length = len(combined_text)

        # 텍스트가 최대 길이를 초과하면 잘라냄 (그래프 구축에는 영향 없음)
        if len(combined_text) > self.MAX_TEXT_LENGTH_FOR_LLM:
            combined_text = combined_text[:self.MAX_TEXT_LENGTH_FOR_LLM]
            combined_text += f"\n\n...(원문 총 {original_length}자, 온톨로지 분석을 위해 앞 {self.MAX_TEXT_LENGTH_FOR_LLM}자를 사용)..."

        message = f"""## 시뮬레이션 요구사항

{simulation_requirement}

## 문서 내용

{combined_text}
"""

        if additional_context:
            message += f"""
## 추가 설명

{additional_context}
"""

        message += """
위 내용을 바탕으로 사회 여론 시뮬레이션에 적합한 엔티티 타입과 관계 타입을 설계하세요.

**반드시 준수해야 하는 규칙**:
1. 정확히 10개의 엔티티 타입을 출력해야 함
2. 마지막 2개는 기본(fallback) 타입이어야 함: Person (개인 기본) 및 Organization (조직 기본)
3. 앞 8개는 텍스트 내용을 기반으로 설계된 구체 타입
4. 모든 엔티티 타입은 현실에서 발언 가능한 주체여야 하며, 추상 개념 불가
5. 속성명에 name, uuid, group_id 등 예약어 사용 불가. full_name, org_name 등을 대신 사용
"""

        return message

    def _validate_and_process(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """결과 검증 및 후처리"""

        # 필수 필드 존재 확인
        if "entity_types" not in result:
            result["entity_types"] = []
        if "edge_types" not in result:
            result["edge_types"] = []
        if "analysis_summary" not in result:
            result["analysis_summary"] = ""

        # 엔티티 타입 검증
        for entity in result["entity_types"]:
            if "attributes" not in entity:
                entity["attributes"] = []
            if "examples" not in entity:
                entity["examples"] = []
            # description 100자 제한
            if len(entity.get("description", "")) > 100:
                entity["description"] = entity["description"][:97] + "..."

        # 관계 타입 검증
        for edge in result["edge_types"]:
            if "source_targets" not in edge:
                edge["source_targets"] = []
            if "attributes" not in edge:
                edge["attributes"] = []
            if len(edge.get("description", "")) > 100:
                edge["description"] = edge["description"][:97] + "..."

        # Zep API 제한: 커스텀 엔티티 타입 최대 10개, 커스텀 엣지 타입 최대 10개
        MAX_ENTITY_TYPES = 10
        MAX_EDGE_TYPES = 10

        # 기본(fallback) 타입 정의
        person_fallback = {
            "name": "Person",
            "description": "Any individual person not fitting other specific person types.",
            "attributes": [
                {"name": "full_name", "type": "text", "description": "Full name of the person"},
                {"name": "role", "type": "text", "description": "Role or occupation"}
            ],
            "examples": ["ordinary citizen", "anonymous netizen"]
        }

        organization_fallback = {
            "name": "Organization",
            "description": "Any organization not fitting other specific organization types.",
            "attributes": [
                {"name": "org_name", "type": "text", "description": "Name of the organization"},
                {"name": "org_type", "type": "text", "description": "Type of organization"}
            ],
            "examples": ["small business", "community group"]
        }

        # 기본 타입 존재 여부 확인
        entity_names = {e["name"] for e in result["entity_types"]}
        has_person = "Person" in entity_names
        has_organization = "Organization" in entity_names

        # 추가가 필요한 기본 타입
        fallbacks_to_add = []
        if not has_person:
            fallbacks_to_add.append(person_fallback)
        if not has_organization:
            fallbacks_to_add.append(organization_fallback)

        if fallbacks_to_add:
            current_count = len(result["entity_types"])
            needed_slots = len(fallbacks_to_add)

            # 추가 후 10개를 초과하면 기존 타입 일부 제거
            if current_count + needed_slots > MAX_ENTITY_TYPES:
                to_remove = current_count + needed_slots - MAX_ENTITY_TYPES
                # 뒤에서 제거 (앞의 중요한 구체 타입 유지)
                result["entity_types"] = result["entity_types"][:-to_remove]

            # 기본 타입 추가
            result["entity_types"].extend(fallbacks_to_add)

        # 최종 상한 초과 방지 (방어적 처리)
        if len(result["entity_types"]) > MAX_ENTITY_TYPES:
            result["entity_types"] = result["entity_types"][:MAX_ENTITY_TYPES]

        if len(result["edge_types"]) > MAX_EDGE_TYPES:
            result["edge_types"] = result["edge_types"][:MAX_EDGE_TYPES]

        return result

    def generate_python_code(self, ontology: Dict[str, Any]) -> str:
        """
        온톨로지 정의를 Python 코드로 변환 (ontology.py 형식)

        Args:
            ontology: 온톨로지 정의

        Returns:
            Python 코드 문자열
        """
        code_lines = [
            '"""',
            '커스텀 엔티티 타입 정의',
            'MiroFish가 자동 생성, 사회 여론 시뮬레이션용',
            '"""',
            '',
            'from pydantic import Field',
            'from zep_cloud.external_clients.ontology import EntityModel, EntityText, EdgeModel',
            '',
            '',
            '# ============== 엔티티 타입 정의 ==============',
            '',
        ]

        # 엔티티 타입 생성
        for entity in ontology.get("entity_types", []):
            name = entity["name"]
            desc = entity.get("description", f"A {name} entity.")

            code_lines.append(f'class {name}(EntityModel):')
            code_lines.append(f'    """{desc}"""')

            attrs = entity.get("attributes", [])
            if attrs:
                for attr in attrs:
                    attr_name = attr["name"]
                    attr_desc = attr.get("description", attr_name)
                    code_lines.append(f'    {attr_name}: EntityText = Field(')
                    code_lines.append(f'        description="{attr_desc}",')
                    code_lines.append(f'        default=None')
                    code_lines.append(f'    )')
            else:
                code_lines.append('    pass')

            code_lines.append('')
            code_lines.append('')

        code_lines.append('# ============== 관계 타입 정의 ==============')
        code_lines.append('')

        # 관계 타입 생성
        for edge in ontology.get("edge_types", []):
            name = edge["name"]
            # PascalCase 클래스명으로 변환
            class_name = ''.join(word.capitalize() for word in name.split('_'))
            desc = edge.get("description", f"A {name} relationship.")

            code_lines.append(f'class {class_name}(EdgeModel):')
            code_lines.append(f'    """{desc}"""')

            attrs = edge.get("attributes", [])
            if attrs:
                for attr in attrs:
                    attr_name = attr["name"]
                    attr_desc = attr.get("description", attr_name)
                    code_lines.append(f'    {attr_name}: EntityText = Field(')
                    code_lines.append(f'        description="{attr_desc}",')
                    code_lines.append(f'        default=None')
                    code_lines.append(f'    )')
            else:
                code_lines.append('    pass')

            code_lines.append('')
            code_lines.append('')

        # 타입 딕셔너리 생성
        code_lines.append('# ============== 타입 설정 ==============')
        code_lines.append('')
        code_lines.append('ENTITY_TYPES = {')
        for entity in ontology.get("entity_types", []):
            name = entity["name"]
            code_lines.append(f'    "{name}": {name},')
        code_lines.append('}')
        code_lines.append('')
        code_lines.append('EDGE_TYPES = {')
        for edge in ontology.get("edge_types", []):
            name = edge["name"]
            class_name = ''.join(word.capitalize() for word in name.split('_'))
            code_lines.append(f'    "{name}": {class_name},')
        code_lines.append('}')
        code_lines.append('')

        # 엣지 source_targets 매핑 생성
        code_lines.append('EDGE_SOURCE_TARGETS = {')
        for edge in ontology.get("edge_types", []):
            name = edge["name"]
            source_targets = edge.get("source_targets", [])
            if source_targets:
                st_list = ', '.join([
                    f'{{"source": "{st.get("source", "Entity")}", "target": "{st.get("target", "Entity")}"}}'
                    for st in source_targets
                ])
                code_lines.append(f'    "{name}": [{st_list}],')
        code_lines.append('}')

        return '\n'.join(code_lines)
