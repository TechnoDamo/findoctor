import { ConsultantTextPage } from "@/components/ConsultantTextPage";

type ConsultantTextRouteProps = {
  searchParams?: {
    prefill?: string;
  };
};

export default function ConsultantTextRoute({ searchParams }: ConsultantTextRouteProps) {
  const initialInput = typeof searchParams?.prefill === "string" ? searchParams.prefill : "";

  return <ConsultantTextPage initialInput={initialInput} />;
}
